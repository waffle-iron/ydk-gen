#  ----------------------------------------------------------------
# Copyright 2016 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------
""" providers.py 
 
   Service Providers module. Current implementation supports the NetconfServiceProvider which
   uses ncclient (a Netconf client library) to provide CRUD services.
   
"""
from ._value_encoder import ValueEncoder
from ydk.errors import YPYDataValidationError, YPYError
from ydk.types import READ, DELETE, Decimal64, Empty, YList
from ydk._core._dm_meta_info import ATTRIBUTE, REFERENCE_ENUM_CLASS, REFERENCE_LIST, \
            REFERENCE_LEAFLIST, REFERENCE_IDENTITY_CLASS, REFERENCE_BITS, REFERENCE_UNION

import logging


def validate_entity(entity, optype):
    i_errors = []
    validate_entity_delegate(entity, optype, i_errors)
    if len(i_errors) > 0:
        _i_errors = map((lambda t: ': '.join(t)), i_errors)
        errmsg = '\n'.join(_i_errors)
        raise YPYDataValidationError(errmsg)


def validate_entity_delegate(entity, optype, i_errors):
    """ Validates the given entity.
    
        This function validates the given entity and it's children. If an entity class
        has any errors , the errors will available in the injected member i_errors ,
        which is a list of tuples of form (<name of the class member>, <error messsage>)
        
        Note this method will raise ydk.errors.YPYDataValidationError if validation fails
    """
    for member in entity.i_meta.meta_info_class_members:
        # print member.mtype, member.name
        value = eval('entity.%s' % member.presentation_name)
        if isinstance(value, READ) or isinstance(value, DELETE):
            continue

        if value is None:
            continue

        # bits
        if hasattr(value, '_has_data') and not value._has_data():
            continue

        # if value is not None:
        if  member.mtype in (ATTRIBUTE, REFERENCE_ENUM_CLASS, REFERENCE_LIST, REFERENCE_LEAFLIST):
        # if  member.mtype==ATTRIBUTE:
            _dm_validate_value(member, value, entity, optype, i_errors)


def _dm_validate_value(meta, value, parent, optype, i_errors):
    # return value#pass
    if value is None:
        return value

    if meta._ptype == 'Empty':
        exec 'from ydk.types import Empty'
    elif meta._ptype == 'Decimal64':
        exec 'from ydk.types import Decimal64'

    if meta.mtype in (REFERENCE_IDENTITY_CLASS,
        REFERENCE_BITS, REFERENCE_ENUM_CLASS, REFERENCE_LIST):
        exec_import = 'from %s import %s' \
            % (meta.pmodule_name, meta.clazz_name.split('.')[0])
        exec exec_import


    if isinstance(value, YList) and meta.mtype == REFERENCE_LIST:
        if optype == 'READ' or meta.max_elements is None:
            max_elements = float('inf')
        else:
            max_elements = meta.max_elements

        if len(value) <= max_elements:
            for v in value:
                _dm_validate_value(meta, v, parent, optype, i_errors)
        else:
            errmsg = "Invalid list length, length = %d" % len(value)
            _handle_error(meta, parent, errmsg, i_errors)
        return value

    elif meta.mtype == REFERENCE_ENUM_CLASS:
        enum_value = value
        exec_import = 'from %s import %s' \
            % (meta.pmodule_name, meta.clazz_name.split('.')[0])
        exec exec_import
        enum_clazz = eval(meta.clazz_name)
        literal_map = enum_clazz._meta_info().literal_map
        enum_found = False
        for yang_enum_name in literal_map:
            literal = literal_map[yang_enum_name]
            if enum_value == getattr(enum_clazz, literal) \
                or enum_value == literal:
                enum_found = True
                break
        if not enum_found:
            errmsg = "Invalid enum, type = %s" % value
            _handle_error(meta, parent, errmsg, i_errors)
        return value

    elif meta.mtype == REFERENCE_LIST:
        if not isinstance(value, eval(meta.clazz_name)):
            errmsg = "Invalid list element type, type = %s" % value
            _handle_error(meta, parent, errmsg, i_errors)
        return value

    elif isinstance(value, eval(meta._ptype)):
        if isinstance(value, int):
            if len(meta._range) > 0:
                valid = False
                for prange in meta._range:
                    if type(prange) == tuple:
                        pmin, pmax = prange
                        if value >= pmin and value <= pmax:
                            valid = True
                            break
                    else:
                        if value == prange:
                            valid = True
                            break
                if not valid:
                    errmsg = "Invalid data or data range, value = %d" % value
                    _handle_error(meta, parent, errmsg, i_errors)

            return value
        elif isinstance(value, str):
            if len(meta._range) > 0:
                valid = False
                for prange in meta._range:
                    if type(prange) == tuple:
                        pmin, pmax = prange
                        if len(value) >= pmin and len(value) <= pmax:
                            valid = True
                            break
                    else:
                        if len(value) == prange:
                            valid = True
                            break
                if not valid:
                    errmsg = "Invalid data or data range, value = %d" % value
                    _handle_error(meta, parent, errmsg, i_errors)

            '''TODO
                if len(meta._pattern) > 0:
                pat_valid = False
                for p in meta._pattern:
                    pat = re.compile(p)
                    if pat.match(value) is not None:
                        pat_valid = True
                        break
                if not pat_valid:
                    errmsg = "Invalid data or data range, value = %s" % value
                    _handle_error(meta, parent, errmsg, i_errors)'''

            return value
        else:
            # enum, etc.
            return value
    # check for type(Empty.SET), type(Empty.UNSET). Needs to be refined
    elif meta._ptype is 'int':
        return value

    elif type(value) == list and meta.mtype == REFERENCE_LEAFLIST:
        # A leaf list.
        min_elements = meta.min_elements if meta.min_elements else 0
        max_elements = meta.max_elements if meta.max_elements else float('inf')

        value_len = len([v for v in value if v is not None])

        if min_elements <= value_len <= max_elements and value_len == len(value):
            for v in value:
                _dm_validate_value(meta, v, parent, optype, i_errors)
        else:
            errmsg = "Invalid leaflist length, length = %d" % value_len
            _handle_error(meta, parent, errmsg, i_errors)
        return value

    elif meta.mtype == REFERENCE_UNION:
        encoded = False
        for contained_member in meta.members:
            # determine what kind of encoding is needed here
            if '' == ValueEncoder().encode(contained_member, {}, value):
                encoded = True
                break
        if not encoded:
            errmsg = "Cannot translate union value"
            _handle_error(meta, parent, errmsg, i_errors)

    else:
        if '' == ValueEncoder().encode(meta, {}, value):
            errmsg = "Cannot encode value"
            _handle_error(meta, parent, errmsg, i_errors)


def _handle_error(meta, parent, errmsg, i_errors):
    services_logger = logging.getLogger('ydk.services')
    entry = (meta.presentation_name, errmsg)
    services_logger.error('Validation error for property %s . Error message %s.' % entry)
    i_errors.append(entry)

    if not hasattr(parent, 'i_errors'):
        parent.i_errors = []
    parent.i_errors.append(entry)
