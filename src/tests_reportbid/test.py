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
from common.utils import pretty_json
from common.utils import print_debug

logger = logging.getLogger(__file__)
here = os.path.dirname(__file__)


class ReportBidTest(BaseTest):

    def joinAdInterestGroup(self, buyer_server, name, bid):
        with MeasureDuration("joinAdInterestGroup"):
            self.driver.get(f"{buyer_server.address}?name={name}&bid={str(bid)}")
            self.assertDriverContainsText('body', 'joined interest group')

    def runAdAuction(self, seller_server, buyer_server):
        with MeasureDuration("runAdAuction"):
            self.driver.get(f"{seller_server.address}?buyer={urllib.parse.quote_plus(buyer_server.address)}")
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD')

    @print_debug
    @measure_time
    @log_exception
    def test__reportbid(self):
        with MockServer(0, 'resources/buyer') as buyer_server,\
                MockServer(0, 'resources/seller') as seller_server:

            bid1 = 17
            self.joinAdInterestGroup(buyer_server, name="test1", bid=bid1)
            bid2 = 53
            self.joinAdInterestGroup(buyer_server, name="test2", bid=bid2)

            self.runAdAuction(seller_server, buyer_server)
            report_win_signals = buyer_server.get_last_request("/reportWin").get_first_json_param('signals')
            logger.info(f"reportWin signals: {pretty_json(report_win_signals)}")
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(bid2)
            assert_that(report_win_signals.get('browserSignals').get('highestScoringOtherBid')).is_equal_to(bid1)

            report_result_signals = seller_server.get_last_request("/reportResult").get_first_json_param('signals')
            logger.info(f"reportResult signals: {pretty_json(report_result_signals)}")
            assert_that(report_result_signals.get('browserSignals').get('bid')).is_equal_to(bid2)
            # scoreAd (in seller.js) returns bid + 100;
            assert_that(report_result_signals.get('browserSignals').get('desirability')).is_equal_to(bid2 + 100)
            assert_that(report_result_signals.get('browserSignals').get('highestScoringOtherBid')).is_equal_to(bid1)
