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


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_basic(self):
        with MockServer(port=8083, directory='resources/seller') as seller_server,  \
                MockServer(port=8101, directory='resources/buyer')  as buyer_server:

            self.joinAdInterestGroup(buyer_server,  name='ig', bid=101)

            self.runAdAuction(seller_server, buyer_server)

            for entry in self.extract_browser_log():
                logger.info(f"browser: {entry}")

            for entry in self.extract_fledge_trace_events():
                logger.info(f"trace: {entry}")

            # wait for the (missing) reports
            logger.info("sleep 1 sec ...")
            time.sleep(1)

            # analyze reports
            report_win_signals = buyer_server.get_last_request('/reportWin').get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(101)


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers(self):
        with MockServer(port=8083, directory='resources/seller') as seller_server, \
                MockServer(port=8101, directory='resources/buyer')  as buyer_server_1, \
                MockServer(port=8102, directory='resources/buyer')  as buyer_server_2, \
                MockServer(port=8103, directory='resources/buyer')  as buyer_server_3, \
                MockServer(port=8104, directory='resources/buyer')  as buyer_server_4, \
                MockServer(port=8105, directory='resources/buyer')  as buyer_server_5, \
                MockServer(port=8106, directory='resources/buyer')  as buyer_server_6, \
                MockServer(port=8107, directory='resources/buyer')  as buyer_server_7, \
                MockServer(port=8108, directory='resources/buyer')  as buyer_server_8, \
                MockServer(port=8109, directory='resources/buyer')  as buyer_server_9, \
                MockServer(port=8110, directory='resources/buyer')  as buyer_server_10, \
                MockServer(port=8111, directory='resources/buyer')  as buyer_server_11, \
                MockServer(port=8112, directory='resources/buyer')  as buyer_server_12, \
                MockServer(port=8113, directory='resources/buyer')  as buyer_server_13, \
                MockServer(port=8114, directory='resources/buyer')  as buyer_server_14, \
                MockServer(port=8115, directory='resources/buyer')  as buyer_server_15, \
                MockServer(port=8116, directory='resources/buyer')  as buyer_server_16:

            self.joinAdInterestGroup(buyer_server_1,  name='ig', bid=101)
            self.joinAdInterestGroup(buyer_server_2,  name='ig', bid=102)
            self.joinAdInterestGroup(buyer_server_3,  name='ig', bid=103)
            self.joinAdInterestGroup(buyer_server_4,  name='ig', bid=104)
            self.joinAdInterestGroup(buyer_server_5,  name='ig', bid=105)
            self.joinAdInterestGroup(buyer_server_6,  name='ig', bid=106)
            self.joinAdInterestGroup(buyer_server_7,  name='ig', bid=107)
            self.joinAdInterestGroup(buyer_server_8,  name='ig', bid=108)
            self.joinAdInterestGroup(buyer_server_9,  name='ig', bid=109)
            self.joinAdInterestGroup(buyer_server_10, name='ig', bid=110)
            self.joinAdInterestGroup(buyer_server_11, name='ig', bid=111)
            self.joinAdInterestGroup(buyer_server_12, name='ig', bid=112)
            self.joinAdInterestGroup(buyer_server_13, name='ig', bid=113)
            self.joinAdInterestGroup(buyer_server_14, name='ig', bid=114)
            self.joinAdInterestGroup(buyer_server_15, name='ig', bid=115)
            self.joinAdInterestGroup(buyer_server_16, name='ig', bid=116)

            self.runAdAuction(seller_server,
                              buyer_server_1,
                              buyer_server_2,
                              buyer_server_3,
                              buyer_server_4,
                              buyer_server_5,
                              buyer_server_6,
                              buyer_server_7,
                              buyer_server_8,
                              buyer_server_9,
                              buyer_server_10,
                              buyer_server_11,
                              buyer_server_12,
                              buyer_server_13,
                              buyer_server_14,
                              buyer_server_15,
                              buyer_server_16)

            # wait for the (missing) reports
            logger.info("sleep 1 sec ...")
            time.sleep(1)

            # analyze reports
            report_win_signals = buyer_server_16.get_last_request('/reportWin').get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(116)
