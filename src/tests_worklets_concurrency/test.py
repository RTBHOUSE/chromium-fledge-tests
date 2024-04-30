# Copyright 2024 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import os
import time
import urllib.parse

from assertpy import assert_that

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import MeasureDuration
from common.utils import log_exception
from common.utils import measure_time
from common.utils import print_debug

logger = logging.getLogger(__file__)
here = os.path.dirname(__file__)


class WorkletsConcurrencyTest(BaseTest):

    def joinAdInterestGroup(self, buyer_server, name, bid):
        with MeasureDuration("joinAdInterestGroup"):
            self.driver.get(buyer_server.address + "?name=" + name + "&bid=" + str(bid))
            self.assertDriverContainsText('body', 'joined interest group')

    def runAdAuction(self, seller_server, buyer_server):
        with MeasureDuration("runAdAuction"):
            self.driver.get(seller_server.address + "?buyer=" + urllib.parse.quote_plus(buyer_server.address))
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD')

    # def fetch_timeout_logs(self):
    #     return filter(lambda entry: entry['source']=='other' and "perBuyerCumulativeTimeout exceeded during bid generation" in entry['message'], self.extract_browser_log())

    @print_debug
    @measure_time
    @log_exception
    def test__perbuyer_cumulative_timeouts_igslow(self):
        with MockServer(port=8081, directory='resources/buyer') as buyer_server,\
                MockServer(port=8083, directory='resources/seller') as seller_server:

            self.joinAdInterestGroup(buyer_server, name='igslow', bid=100)
            self.runAdAuction(seller_server, buyer_server)

            # check browser logs
            # assert_that(list(self.fetch_timeout_logs())).is_not_empty()

            # wait for the (missing) reports
            logger.info("sleep 1 sec ...")
            time.sleep(1)

            # analyze reports
            report_win_signals = buyer_server.get_last_request('/reportWin').get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(100)
