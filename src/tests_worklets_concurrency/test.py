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
        s.__exit__(None, None, None)


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

    assert_that(count_par).is_equal_to(0)
    assert_that(count_all).is_equal_to(count_b+count_e)
    assert_that(count_b).is_equal_to(count_e)
    assert_that(count_max).is_less_than_or_equal_to(count_b)
    return (count_b, count_max)


def concurrency_level_with_filter(fledge_trace_sorted, name_pattern):
    patt_comp = re.compile(name_pattern, re.ASCII | re.IGNORECASE)
    (count_events, count_par) = concurrency_level(filter(lambda x: patt_comp.match(x['name']), fledge_trace_sorted))
    logger.info(f"concurrency level ({name_pattern}): {count_par} (total: {count_events})")
    return (count_events, count_par)


def precomputeBid(buyer, ig):
    """
    Given the buyer index (0+) and interest group index (0+) precomputes the bid value
    to be used in the testcase.

    Note: using integer bid value > 256 will result in stochastic rounding to
    an 8-bit mantissa/8-bit exponent float number on recent Chrome versions
    (such behavior is compliant with the Fledge specs).
    """
    bid = 5 * buyer + ig
    assert 0 <= bid
    assert bid < 256
    return bid


class WorkletsConcurrencyTest(BaseTest):
    """
    This test suite aims to assess bidding worklets concurrency level. It demonstrates an upper limit
    of 10 bidding worklets, times the number of IGs per buyer, running in parallel.
    """

    def joinAdInterestGroup(self, buyer_server, name, execution_mode, bid):
        assert execution_mode in ['compatibility', 'frozen-context', 'group-by-origin']
        with MeasureDuration("joinAdInterestGroup"):
            self.driver.get(buyer_server.address + "?name=" + name + "&executionMode=" + execution_mode + "&bid=" + str(bid))
            self.assertDriverContainsText('body', 'joined interest group')

    def runAdAuction(self, seller_server, *buyer_servers):
        with MeasureDuration("runAdAuction"):
            seller_url_params = "?buyer=" + "&buyer=".join([urllib.parse.quote_plus(bs.address) for bs in buyer_servers])
            self.driver.get(seller_server.address + seller_url_params)
            self.findFrameAndSwitchToIt()
            self.assertDriverContainsText('body', 'TC AD')

    def genericTest(self, buyers, buyer_igs, auctions, execution_mode):
        assert 1 <= buyers
        assert 1 <= buyer_igs
        assert 1 <= auctions
        assert execution_mode in ['compatibility', 'frozen-context', 'group-by-origin']

        with MockServer(port=8483, directory='resources/seller') as seller_server:
            shutdown_ok = False

            try:
                # Create buyer servers
                buyer_servers = generate_buyers(buyers, 8500)

                # Join ad interest groups
                for i in range(0, buyers):
                    for j in range(0, buyer_igs):
                        self.joinAdInterestGroup(
                            buyer_servers[i],
                            name='ig_'+str(i)+'_'+str(j),
                            execution_mode=execution_mode,
                            bid=precomputeBid(i, j))

                # Run a number of auctions ...
                for testcase in range(0, auctions):
                    self.runAdAuction(seller_server, *buyer_servers)

                # shutdown servers
                shutdown_servers(buyer_servers)
                shutdown_ok = True

                # Inspect fledge trace events
                fledge_trace = self.extract_fledge_trace_events()
                logger.info(f"fledge_trace: {len(fledge_trace)} events")

                # inspect bidder worklet events
                (count_events, count_par) = concurrency_level_with_filter(fledge_trace, 'bidder_worklet_generate_bid')
                assert_that(count_events).is_equal_to(auctions * buyers * buyer_igs)

                ################################################################
                # Exactly 10 bidding worklets (or less, if not enough buyers),
                # times the number of IGs per buyer, running in parallel!
                ################################################################
                expected_par = min(10, buyers) * buyer_igs
                assert_that(count_par, description=f"Exactly {expected_par} bidding worklets running in parallel").is_equal_to(expected_par)

                # inspect generate_bid events
                (count_events, count_par) = concurrency_level_with_filter(fledge_trace, 'generate_bid')
                assert_that(count_events).is_equal_to(auctions * buyers * buyer_igs)

                # wait for the (missing) reports
                logger.info("sleep 1 sec ...")
                time.sleep(1)

                # analyze the reports
                report_win_signals = buyer_servers[-1].get_last_request('/reportWin').get_first_json_param('signals')
                assert_that(report_win_signals.get('browserSignals').get('bid')).is_equal_to(precomputeBid(buyers-1, buyer_igs-1))
            finally:
                if not shutdown_ok:
                    shutdown_servers(buyer_servers)


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_basic(self):
        """1 seller, 1 buyer, 1 interest group, 1 auction."""
        with MockServer(port=8083, directory='resources/seller') as seller_server,  \
                MockServer(port=8101, directory='resources/buyer')  as buyer_server:

            self.joinAdInterestGroup(buyer_server,  name='ig', execution_mode='compatibility', bid=101)
            self.runAdAuction(seller_server, buyer_server)

            for entry in self.extract_browser_log():
                logger.info(f"browser: {entry}")

            # inspect fledge trace events
            fledge_trace = self.extract_fledge_trace_events()

            for entry in fledge_trace:
                logger.info(f"trace: {entry}")

            (count_events, count_par) = concurrency_level_with_filter(fledge_trace, 'generate_bid')
            assert_that(count_events).is_equal_to(1)
            assert_that(count_par).is_equal_to(1)

            (count_events, count_par) = concurrency_level_with_filter(fledge_trace, 'bidder_worklet_generate_bid')
            assert_that(count_events).is_equal_to(1)
            assert_that(count_par).is_equal_to(1)

            (count_events, count_par) = concurrency_level_with_filter(fledge_trace, '.*worklet.*')
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
    def test__worklets_5_buyers_1_ig_3_auctions_compatibility(self):
        self.genericTest(5, 1, 3, 'compatibility')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_5_buyers_1_ig_3_auctions_frozencontext(self):
        self.genericTest(5, 1, 3, 'frozen-context')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_5_buyers_1_ig_3_auctions_groupbyorigin(self):
        self.genericTest(5, 1, 3, 'group-by-origin')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_5_buyers_6_ig_3_auctions_compatibility(self):
        self.genericTest(5, 6, 3, 'compatibility')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_5_buyers_6_ig_3_auctions_frozencontext(self):
        self.genericTest(5, 6, 3, 'frozen-context')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_5_buyers_6_ig_3_auctions_groupbyorigin(self):
        self.genericTest(5, 6, 3, 'group-by-origin')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers_1_ig_3_auctions_compatibility(self):
        self.genericTest(16, 1, 3, 'compatibility')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers_1_ig_3_auctions_frozencontext(self):
        self.genericTest(16, 1, 3, 'frozen-context')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers_1_ig_3_auctions_groupbyorigin(self):
        self.genericTest(16, 1, 3, 'group-by-origin')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers_7_ig_3_auctions_compatibility(self):
        self.genericTest(16, 7, 3, 'compatibility')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers_7_ig_3_auctions_frozencontext(self):
        self.genericTest(16, 7, 3, 'frozen-context')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_16_buyers_7_ig_3_auctions_groupbyorigin(self):
        self.genericTest(16, 7, 3, 'group-by-origin')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_32_buyers_1_ig_2_auctions_compatibility(self):
        self.genericTest(32, 1, 2, 'compatibility')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_32_buyers_1_ig_2_auctions_frozencontext(self):
        self.genericTest(32, 1, 2, 'frozen-context')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_32_buyers_1_ig_2_auctions_groupbyorigin(self):
        self.genericTest(32, 1, 2, 'group-by-origin')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_32_buyers_17_ig_2_auctions_compatibility(self):
        self.genericTest(32, 17, 2, 'compatibility')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_32_buyers_17_ig_2_auctions_frozencontext(self):
        self.genericTest(32, 17, 2, 'frozen-context')


    @print_debug
    @measure_time
    @log_exception
    def test__worklets_32_buyers_17_ig_2_auctions_groupbyorigin(self):
        self.genericTest(32, 17, 2, 'group-by-origin')
