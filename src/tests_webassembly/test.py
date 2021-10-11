# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import print_debug, measure_time, log_exception, MeasureDuration, pretty_json

logger = logging.getLogger(__file__)


class FunctionalTest(BaseTest):

    @print_debug
    @measure_time
    @log_exception
    def test__basic_webassembly(self):
        with MockServer(9021, '/home/usertd/tests/tests_webassembly/resources/buyer') as buyer_server,\
                MockServer(9022, '/home/usertd/tests/tests_webassembly/resources/seller') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address)
                WebDriverWait(self.driver, 5) \
                    .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
                self.assertDriverContainsText('body', 'TC AD')

        report_result_signals = seller_server.get_first_request("/reportResult").get_first_json_param('signals')
        logger.info(f"reportResult() signals: {pretty_json(report_result_signals)}")

        report_win_signals = buyer_server.get_first_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")

        # we use stub scoreAd() that returns generateBid() duration in ms as its result
        bid_duration_ms = report_result_signals['browserSignals']['desirability']
        logger.info(f"generateBid took: {bid_duration_ms} ms")
