# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import os
import urllib.parse

from assertpy import assert_that

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import MeasureDuration
from common.utils import log_exception
from common.utils import measure_time
from common.utils import print_debug

from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__file__)
here = os.path.dirname(__file__)


class DebuggingApiTest(BaseTest):

    def joinAdInterestGroup(self, buyer_server, name, bid):
        with MeasureDuration("joinAdInterestGroup"):
            self.driver.get(buyer_server.address + "?name=" + name + "&bid=" + str(bid))
            self.assertDriverContainsText('body', 'joined interest group')

    def runAdAuction(self, seller_server, buyer_server):
        with MeasureDuration("runAdAuction"):
            self.driver.get(seller_server.address + "?buyer=" + urllib.parse.quote_plus(buyer_server.address))
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD')

    @print_debug
    @measure_time
    @log_exception
    def test__debugging_api(self):
        with MockServer(port=8081, directory='resources/buyer') as buyer_server,\
                MockServer(port=8083, directory='resources/seller') as seller_server:

            self.joinAdInterestGroup(buyer_server, name='loser', bid=1)
            self.joinAdInterestGroup(buyer_server, name='winner', bid=2)

            assert_that(self.runAdAuction).raises(TimeoutException).when_called_with(seller_server, buyer_server).starts_with("Message: Failed to find frame in given time 5 seconds.")

            assert_that(buyer_server.get_last_request("/reportWin")).is_none()
            assert_that(buyer_server.get_last_request("/debugReportLoss")).is_none()
            assert_that(buyer_server.get_last_request("/debugReportWin")).is_none()
