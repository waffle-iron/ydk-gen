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

import ydk.types as ytypes
import unittest
# from errors import YPYDataValidationError 

from ydk.services import CRUDService
from ydk.providers import NetconfServiceProvider
from ydk.types import Empty, DELETE, Decimal64
from tests.compare import is_equal
from ydk.errors import YPYError, YPYDataValidationError
from ydk.models.bgp import bgp
from ydk.models.routing.routing_policy import DefaultPolicyTypeEnum, RoutingPolicy

class SanityTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.ncc = NetconfServiceProvider(address='127.0.0.1', port=12022)
        self.crud = CRUDService()

    @classmethod
    def tearDownClass(self):
        self.ncc.close()

    def setUp(self):
        pass
        # print "\nIn method", self._testMethodName
        # bgp_cfg = bgp.Bgp()
        # self.crud.delete(self.ncc, bgp_cfg)

    def tearDown(self):
        pass

    def test_bgp(self):
        # Bgp.Global.AfiSafis.AfiSafi.ApplyPolicy is not supported
        bgp_cfg = bgp.Bgp()
        ipv4_afsf = bgp_cfg.global_.afi_safis.AfiSafi()
        ipv4_afsf.afi_safi_name = 'ipv4-unicast'
        ipv4_afsf.apply_policy.config.default_export_policy = \
            DefaultPolicyTypeEnum.ACCEPT_ROUTE
        bgp_cfg.global_.afi_safis.afi_safi.append(ipv4_afsf)

        self.assertRaises(YPYDataValidationError,
            self.crud.create, self.ncc, bgp_cfg)


if __name__ == '__main__':
    unittest.main()
