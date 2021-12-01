# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import os

import urllib.parse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import MeasureDuration
from common.utils import log_exception
from common.utils import measure_time
from common.utils import pretty_json
from common.utils import print_debug

logger = logging.getLogger(__file__)
here = os.path.dirname(__file__)


class TensorflowTest(BaseTest):

    @print_debug
    @measure_time
    @log_exception
    def test__tensorflow(self):
        with MockServer(0, 'resources/buyer') as buyer_server,\
                MockServer(0, 'resources/seller') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address + "?buyer=" + urllib.parse.quote_plus(buyer_server.address))
                WebDriverWait(self.driver, 6)\
                    .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
                self.assertDriverContainsText('body', 'TC AD')

        report_result_signals = seller_server.get_last_request("/reportResult").get_first_json_param('signals')
        logger.info(f"reportResult() signals: {pretty_json(report_result_signals)}")

        report_win_signals = buyer_server.get_last_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")

        # we use stub scoreAd() that returns generateBid() duration in ms as its result
        bid_duration_ms = report_result_signals['browserSignals']['desirability']
        logger.info(f"generateBid took: {bid_duration_ms} ms")
