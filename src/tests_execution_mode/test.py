# Copyright 2024 RTBHOUSE. All rights reserved.
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


class ExecutionModeTest(BaseTest):

    EXECUTION_MODE_compatibility: str = "compatibility"

    def joinAdInterestGroup(self, buyer_server, name, executionMode, bid):
        with MeasureDuration("joinAdInterestGroup"):
            self.driver.get(buyer_server.address + "?name=" + name + "&executionMode=" + executionMode + "&bid=" + str(bid))
            self.assertDriverContainsText('body', 'joined interest group')

    def runAdAuction(self, seller_server, buyer_server):
        with MeasureDuration("runAdAuction"):
            self.driver.get(seller_server.address + "?buyer=" + urllib.parse.quote_plus(buyer_server.address))
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD')

    @print_debug
    @measure_time
    @log_exception
    def test__execution_mode_compatibility(self):
        with MockServer(port=8081, directory='resources/buyer') as buyer_server,\
                MockServer(port=8083, directory='resources/seller') as seller_server:

            self.joinAdInterestGroup(buyer_server, name='igslow', executionMode=self.EXECUTION_MODE_compatibility, bid=100)

            # run the auction
            self.runAdAuction(seller_server, buyer_server)

            # analyze reports
            report_win_signals = buyer_server.get_last_request('/reportWin').get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(100)
