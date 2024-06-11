# Copyright 2024 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import os
import re
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


def generate_buyers(count, start_port=8500):
    servers = []
    for i in range(0,count):
        ms = MockServer(port=start_port+i+1, directory='resources/buyer')
        ms.__enter__()
        servers.append(ms)
    return servers


def shutdown_servers(servers):
    for s in servers:
        s.__exit__(None,None,None)


def concurrency_level(fledge_trace_sorted):
    count_max = 0
    count_par = 0
    count_b = 0
    count_e = 0
    count_all = 0

    for x in fledge_trace_sorted:
        if 'b' == x['ph']:
            count_par += 1
            count_b += 1
        if 'e' == x['ph']:
            count_par -= 1
            count_e += 1

        count_max = max(count_max, count_par)
        count_all += 1

    assert_that(count_all).is_equal_to(count_b+count_e)
    assert_that(count_b).is_equal_to(count_e)
    return (count_b,count_max)


def concurrency_level_with_filter(fledge_trace_sorted, name_pattern):
    patt_comp = re.compile(name_pattern, re.ASCII | re.IGNORECASE)
    (count_events,count_par) = concurrency_level(filter(lambda x: patt_comp.match(x['name']), fledge_trace_sorted))
    logger.info(f"concurrency level ({name_pattern}): {count_par} (total: {count_events})")
    return (count_events,count_par)


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

            # inspect fledge trace events
            fledge_trace = self.extract_fledge_trace_events()

            for entry in fledge_trace:
                logger.info(f"trace: {entry}")

            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'generate_bid')
            assert_that(count_events).is_equal_to(1)
            assert_that(count_par).is_equal_to(1)

            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'bidder_worklet_generate_bid')
            assert_that(count_events).is_equal_to(1)
            assert_that(count_par).is_equal_to(1)

            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, '.*worklet.*')
            assert_that(count_events).is_equal_to(5)
            assert_that(count_par).is_equal_to(1)

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
        """1 seller, 16 buyers, 1 interest group, 1 auction."""
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

            # Join interest groups
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

            # inspect fledge trace events
            fledge_trace = self.extract_fledge_trace_events()

            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'generate_bid')
            assert_that(count_events).is_equal_to(16)
            assert_that(count_par).is_greater_than_or_equal_to(2)  # at least 2 generate_bid calls at the same time

            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'bidder_worklet_generate_bid')
            assert_that(count_events).is_equal_to(16)
            assert_that(count_par).is_greater_than_or_equal_to(4)  # at least 4 worklets running at the same time

            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, '.*worklet.*')
            assert_that(count_events).is_equal_to(35)

            # wait for the (missing) reports
            logger.info("sleep 1 sec ...")
            time.sleep(1)

            # analyze reports
            report_win_signals = buyer_server_16.get_last_request('/reportWin').get_first_json_param('signals')
            assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(116)


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers_12_auctions(self):
        """1 seller, 16 buyers, 1 interest group, 12 auctions."""
        with MockServer(port=8283, directory='resources/seller') as seller_server, \
                MockServer(port=8301, directory='resources/buyer')  as buyer_server_1, \
                MockServer(port=8302, directory='resources/buyer')  as buyer_server_2, \
                MockServer(port=8303, directory='resources/buyer')  as buyer_server_3, \
                MockServer(port=8304, directory='resources/buyer')  as buyer_server_4, \
                MockServer(port=8305, directory='resources/buyer')  as buyer_server_5, \
                MockServer(port=8306, directory='resources/buyer')  as buyer_server_6, \
                MockServer(port=8307, directory='resources/buyer')  as buyer_server_7, \
                MockServer(port=8308, directory='resources/buyer')  as buyer_server_8, \
                MockServer(port=8309, directory='resources/buyer')  as buyer_server_9, \
                MockServer(port=8310, directory='resources/buyer')  as buyer_server_10, \
                MockServer(port=8311, directory='resources/buyer')  as buyer_server_11, \
                MockServer(port=8312, directory='resources/buyer')  as buyer_server_12, \
                MockServer(port=8313, directory='resources/buyer')  as buyer_server_13, \
                MockServer(port=8314, directory='resources/buyer')  as buyer_server_14, \
                MockServer(port=8315, directory='resources/buyer')  as buyer_server_15, \
                MockServer(port=8316, directory='resources/buyer')  as buyer_server_16:

            # Join interest groups
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

            # Run a number of auctions ...
            testcase_count = 12
            for testcase in range(0, testcase_count):
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

            # Inspect fledge trace events
            fledge_trace = self.extract_fledge_trace_events()
            logger.info(f"fledge_trace: {len(fledge_trace)} events")

            # Check concurrency level of generate_bid
            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'generate_bid')
            assert_that(count_events).is_equal_to(testcase_count * 16)
            assert_that(count_par).is_greater_than_or_equal_to(4)  # at least 4 generate_bid calls at the same time

            # Check concurrency level of generate_bid worklet
            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'bidder_worklet_generate_bid')
            assert_that(count_events).is_equal_to(testcase_count * 16)

            # Exactly 10 worklets running at the same time!
            assert_that(count_par).is_equal_to(10)


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_32_buyers_12_auctions(self):
        """1 seller, 32 buyers, 1 interest group, 12 auctions."""
        with MockServer(port=8483, directory='resources/seller') as seller_server:
            buyer_servers = generate_buyers(32,8500)

            # Join interest groups
            for i in range(0,32):
                self.joinAdInterestGroup(buyer_servers[i],  name='ig', bid=100+i)

            # Run a number of auctions ...
            testcase_count = 12
            for testcase in range(0, testcase_count):
                self.runAdAuction(seller_server, *buyer_servers)

            # shutdown servers
            shutdown_servers(buyer_servers)

            # Inspect fledge trace events
            fledge_trace = self.extract_fledge_trace_events()
            logger.info(f"fledge_trace: {len(fledge_trace)} events")

            # Check concurrency level of generate_bid
            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'generate_bid')
            assert_that(count_events).is_equal_to(testcase_count * 32)
            assert_that(count_par).is_greater_than_or_equal_to(4)  # at least 4 generate_bid calls at the same time

            # Check concurrency level of generate_bid worklet
            (count_events,count_par) = concurrency_level_with_filter(fledge_trace, 'bidder_worklet_generate_bid')
            assert_that(count_events).is_equal_to(testcase_count * 32)

            # Exactly 10 worklets running at the same time!
            assert_that(count_par).is_equal_to(10)
