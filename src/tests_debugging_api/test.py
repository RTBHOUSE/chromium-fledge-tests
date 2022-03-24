# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import os
import urllib.parse
import time

from assertpy import assert_that

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import MeasureDuration
from common.utils import log_exception
from common.utils import measure_time
from common.utils import print_debug

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
        with MockServer(0, 'resources/buyer') as buyer_server,\
                MockServer(0, 'resources/seller') as seller_server:

            self.joinAdInterestGroup(buyer_server, name='loser', bid=1)
            self.joinAdInterestGroup(buyer_server, name='winner', bid=2)

            self.runAdAuction(seller_server, buyer_server)
            report_win_signals = buyer_server.get_last_request('/reportWin').get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(2)

            debug_loss_signals = buyer_server.get_last_request("/debugReportLoss").get_first_json_param('signals')
            assert_that(debug_loss_signals.get('interestGroup').get('name')).is_equal_to('loser')

            debug_win_signals = buyer_server.get_last_request("/debugReportWin").get_first_json_param('signals')
            assert_that(debug_win_signals.get('interestGroup').get('name')).is_equal_to('winner')
