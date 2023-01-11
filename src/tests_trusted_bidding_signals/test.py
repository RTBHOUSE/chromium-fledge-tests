# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging

from assertpy import assert_that

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import MeasureDuration
from common.utils import log_exception
from common.utils import measure_time
from common.utils import pretty_json
from common.utils import print_debug

logger = logging.getLogger(__file__)


class TrustedBiddingSignalsTest(BaseTest):

    @print_debug
    @measure_time
    @log_exception
    def test__should_pass_trusted_bidding_signals(self):
        with MockServer(port=8101, directory='resources/buyer') as buyer_server,\
                MockServer(port=8102, directory='resources/seller') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address)
                self.findFrameAndSwitchToIt()
                self.assertDriverContainsText('body', 'TC AD 1')

        report_win_signals = buyer_server.get_last_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")
        # generateBid() in this test case uses one of trustedBiddingSignals as a bid value
        assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(15)
