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

""" errors.py 
 
   Contains types representing the Exception hierarchy in YDK
   
"""
from lxml import etree
from enum import Enum


class YPYErrorCode(Enum):
    INVALID_UNION_VALUE = 'Cannot translate union value'
    INVALID_ENCODE_VALUE = 'Cannot encode value'
    INVALID_HIERARCHY_PARENT = 'Parent is not set. \
                    Parent Hierarchy cannot be determined'
    INVALID_HIERARCHY_KEY = 'Key value is not set. \
                    Parent hierarchy cannot be constructed'
    INVALID_RPC = 'Object is not an RPC, cannot execute non-RPC object.'
    INVALID_MODIFY = 'Entity is read-only, cannot modify a read-only entity.'
    SERVER_REJ = 'Server rejected request.'
    SERVER_COMMIT_ERR = 'Server reported an error while committing change.'


class YPYError(Exception):
    ''' Base Exception for YDK Errors '''
    def __init__(self, error_code=None, error_msg=None):
        self.error_code = error_code
        self.error_msg = error_msg

    def __str__(self):
        ret = []
        if self.error_code is not None:
            ret.append(self.error_code.value)
        if self.error_msg is not None:
            parser = etree.XMLParser(remove_blank_text=True)
            root = etree.XML(self.error_msg.xml, parser)
            for r in root.iter():
                tag = r.tag[r.tag.rfind('}') + 1 :]
                if r.text is not None:
                    ret.append('\t{}: {}'.format(tag, r.text.strip()))
        return '\n'.join(ret)


class YPYDataValidationError(YPYError):
    '''
    Exception for Client Side Data Validation

    Type Validation\n
    --------
    Any data validation error encountered that is related to type \
    validation encountered does not raise an Exception right away. 
    
    To uncover as many client side issues as possible, \
    an i_errors list is injected in the parent entity of any entity \
    with issues. The items added to this i_errors list captures the \
    object type that caused the error as well as an error message.

    '''
    pass
