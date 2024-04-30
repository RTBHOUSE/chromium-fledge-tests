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

    def runAdAuction(self, seller_server, *buyer_servers):
        with MeasureDuration("runAdAuction"):
            seller_url_params = "?buyer=" + "&buyer=".join([urllib.parse.quote_plus(bs.address) for bs in buyer_servers])
            self.driver.get(seller_server.address + seller_url_params)
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD')

    # def fetch_timeout_logs(self):
    #     return filter(lambda entry: entry['source']=='other' and "perBuyerCumulativeTimeout exceeded during bid generation" in entry['message'], self.extract_browser_log())

    @print_debug
    @measure_time
    @log_exception
    def test__worklets_simple(self):
        with MockServer(port=8083, directory='resources/seller') as seller_server,  \
            MockServer(port=8101, directory='resources/buyer')  as buyer_server_1,  \
            MockServer(port=8102, directory='resources/buyer')  as buyer_server_2,  \
            MockServer(port=8103, directory='resources/buyer')  as buyer_server_3:

            self.joinAdInterestGroup(buyer_server_1, name='ig', bid=101)
            self.joinAdInterestGroup(buyer_server_2, name='ig', bid=102)
            self.joinAdInterestGroup(buyer_server_3, name='ig', bid=103)
            self.runAdAuction(seller_server, buyer_server_1, buyer_server_2)

            # check browser logs
            # assert_that(list(self.fetch_timeout_logs())).is_not_empty()

            # wait for the (missing) reports
            logger.info("sleep 1 sec ...")
            time.sleep(1)

            # analyze reports
            report_win_signals = buyer_server_2.get_last_request('/reportWin').get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(102)
