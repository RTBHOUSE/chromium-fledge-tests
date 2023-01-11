# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import time

from assertpy import assert_that

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import log_exception
from common.utils import measure_time
from common.utils import print_debug

logger = logging.getLogger(__file__)


class DailyUpdateTest(BaseTest):

    @print_debug
    @measure_time
    @log_exception
    def test__should_update(self):
        with MockServer(port=8201, directory='resources/buyer') as buyer_server,\
                MockServer(port=8202, directory='resources/seller') as seller_server:

            # join interest group
            self.driver.get(buyer_server.address)
            self.assertDriverContainsText('body', 'joined interest group')

            # run auction
            self.driver.get(seller_server.address)
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD 1')
            report_win_signals = buyer_server.get_last_request("/reportWin").get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('renderUrl')) \
                .is_equal_to("https://localhost:8201/ad-1.html")

            # update interest group
            self.driver.get(buyer_server.address + "/do_update.html")
            self.assertDriverContainsText('body', 'updated interest group')

            # wait for the browser to download updates
            time.sleep(5)

            # run auction again to check if the update was successful
            # (note that now we expect a different ad to win)
            self.driver.get(seller_server.address)
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD 2')
            report_win_signals = buyer_server.get_last_request("/reportWin").get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('renderUrl')) \
                .is_equal_to("https://localhost:8201/ad-2.html")
