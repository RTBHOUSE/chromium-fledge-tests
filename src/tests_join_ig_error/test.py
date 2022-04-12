# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import os

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import MeasureDuration
from common.utils import log_exception
from common.utils import measure_time
from common.utils import print_debug

logger = logging.getLogger(__file__)
here = os.path.dirname(__file__)


class JoinIgTest(BaseTest):

    def joinAdInterestGroup(self, buyer_server, name, bid):
        with MeasureDuration("joinAdInterestGroup"):
            self.driver.get(buyer_server.address + "?name=" + name + "&bid=" + str(bid))
            print("==================")
            print(self.driver.find_element_by_xpath("/html/body").text)
            print("==================")

    @print_debug
    @measure_time
    @log_exception
    def test__join_ig(self):
        with MockServer(0, 'resources/buyer') as buyer_server:
            self.joinAdInterestGroup(buyer_server, name='test', bid=1)
