# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import json
import logging
import os
import threading
import time
import unittest
from datetime import datetime
from functools import wraps

from assertpy import assert_that
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from mockserver import MockServer

logger = logging.getLogger(__file__)
SERVICE_LOG_PATH = '/home/usertd/logs/chr2.log'


class MeasureDuration:
    def __init__(self, method_name):
        self.method_name = method_name
        self.start = None
        self.finish = None

    def __enter__(self):
        self.start = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish = datetime.now()
        logger.info(f"{self.method_name} took {self.duration()}")

    def duration(self):
        return self.finish - self.start


class TrackFile:
    def __init__(self, path):
        self.stop = False
        self.path = path
        self.thread = threading.Thread(target=self.track)

    def __enter__(self):
        self.thread.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop = True
        self.thread.join()

    def track(self):
        with open(self.path) as f:
            while not self.stop:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                elif '[rtb-chromium-debug]' in line:
                    logger.info(line.rstrip())
            # reading rest of the file after stop
            for line in f.readlines():
                if '[rtb-chromium-debug]' in line:
                    logger.info(line.rstrip())


def measure_time(method):
    @wraps(method)
    def inner_measure_time(self, *args, **kwargs):
        with MeasureDuration(f"{self.__class__.__name__}.{method.__name__,}") as m:
            return method(self, *args, **kwargs)
    return inner_measure_time


def log_exception(method):
    @wraps(method)
    def inner_log_exception(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except BaseException:
            logger.warning(self.driver.page_source)
            raise
    return inner_log_exception


def print_debug(method):
    @wraps(method)
    def inner_print_debug(self, *args, **kwargs):
        with TrackFile(SERVICE_LOG_PATH):
            return method(self, *args, **kwargs)
    return inner_print_debug


def pretty_json(data):
    return json.dumps(data, indent=2, sort_keys=True)


class InitialTest(unittest.TestCase):
    def setUp(self) -> None:
        # https://peter.sh/experiments/chromium-command-line-switches/
        options = webdriver.ChromeOptions()
        if os.path.isfile('/home/usertd/chromium-custom/chrome'):
            logger.info("using custom chromium build")
            options.binary_location = '/home/usertd/chromium-custom/chrome'
        else:
            logger.info("using official chrome build")
            options.binary_location = '/home/usertd/chrome-linux/chrome'
        # FIXME headless chrome does not work with fledge, https://bugs.chromium.org/p/chromium/issues/detail?id=1229652
        # options.headless = True
        options.add_argument('--no-sandbox')
        options.add_argument('--no-zygote')
        # FIXME headless chrome does not work with fledge, https://bugs.chromium.org/p/chromium/issues/detail?id=1229652
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--user-data-dir=/tmp/profile123')
        options.add_argument('--user-agent=rtbfledgetests')
        options.add_argument('--enable-features=FledgeInterestGroups,FledgeInterestGroupAPI')
        driver = webdriver.Chrome('/home/usertd/chromedriver_linux64/chromedriver', options=options,
                                  service_args=['--enable-chrome-logs'],
                                  service_log_path=SERVICE_LOG_PATH)
        self.driver = driver

    def tearDown(self) -> None:
        self.driver.quit()

    def assertDriverContainsText(self, css_selector, text, timeout=5):
        exc_msg = f'Failed to find text "{text}" in element "{css_selector}" '\
                  f'in given time {timeout} seconds.'
        WebDriverWait(self.driver, timeout)\
            .until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, css_selector), text), exc_msg)

    def test__driver_should_work(self):
        self.driver.get('https://techblog.rtbhouse.com/')
        self.assertDriverContainsText('#bs-example-navbar-collapse-1 > ul', 'HOME')

    @print_debug
    @log_exception
    def test__should_report_win(self):
        with MockServer(8081, '/home/usertd/src/test/resources/buyer1') as buyer_server,\
                MockServer(8082, '/home/usertd/src/test/resources/publisher1') as publisher_server,\
                MockServer(8083, '/home/usertd/src/test/resources/seller1') as seller_server:

            self.driver.get(buyer_server.address)
            self.assertDriverContainsText('h1', 'Hello')
            self.driver.get(publisher_server.address)

    @print_debug
    @log_exception
    def test__should_show_ad_jeff(self):
        self.driver.get('https://www.trycontra.com/test/td/join.html')
        self.assertDriverContainsText('body', 'joined interest group')

        self.driver.get('https://www.jefftk.com/test/td/auction.html')
        WebDriverWait(self.driver, 5) \
            .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
        logger.info(self.driver.page_source)
        self.assertDriverContainsText('body', 'TC AD 1')

    @print_debug
    @measure_time
    @log_exception
    def test__should_show_ad_our(self):
        with MockServer(8091, '/home/usertd/src/test/resources/buyer2') as buyer_server,\
                MockServer(8092, '/home/usertd/src/test/resources/seller2') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address)
                WebDriverWait(self.driver, 5)\
                    .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
                self.assertDriverContainsText('body', 'TC AD 1')

        report_result_signals = seller_server.get_first_request("/reportResult").get_first_json_param('signals')
        logger.info(f"reportResult() signals: {pretty_json(report_result_signals)}")
        assert_that(report_result_signals.get('browserSignals').get('interestGroupOwner'))\
            .is_equal_to("https://fledge-tests.creativecdn.net:8091")
        assert_that(report_result_signals.get('browserSignals').get('renderUrl')) \
            .is_equal_to("https://fledge-tests.creativecdn.net:8091/ad-1.html")

        report_win_signals = buyer_server.get_first_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")
        assert_that(report_win_signals.get('browserSignals').get('interestGroupOwner')) \
            .is_equal_to("https://fledge-tests.creativecdn.net:8091")
        assert_that(report_win_signals.get('browserSignals').get('renderUrl')) \
            .is_equal_to("https://fledge-tests.creativecdn.net:8091/ad-1.html")

    @print_debug
    @measure_time
    @log_exception
    def test__check_nn_with_random_weights_computation_time(self):
        with MockServer(9001, '/home/usertd/src/test/resources/buyer3') as buyer_server,\
                MockServer(9002, '/home/usertd/src/test/resources/seller3') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address)
                WebDriverWait(self.driver, 5)\
                    .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
                self.assertDriverContainsText('body', 'TC AD')

        report_result_signals = seller_server.get_first_request("/reportResult").get_first_json_param('signals')
        logger.info(f"reportResult() signals: {pretty_json(report_result_signals)}")

        report_win_signals = buyer_server.get_first_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")

        # to be able to measure bidding worklet time you should use custom-built version of chromium
        # with a patch like this: https://github.com/RTBHOUSE/chromium/commits/auction_timer
        if 'bid_duration' in report_result_signals.get('browserSignals'):
            bid_duration_ms = int(report_result_signals.get('browserSignals').get('bid_duration')) / 1000
            logger.info(f"generateBid took: {bid_duration_ms} ms")

    @print_debug
    @measure_time
    @log_exception
    def test__check_nn_with_static_weights_computation_time(self):
        with MockServer(9011, '/home/usertd/src/test/resources/buyer4') as buyer_server,\
                MockServer(9012, '/home/usertd/src/test/resources/seller4') as seller_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get(seller_server.address)
                WebDriverWait(self.driver, 5)\
                    .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
                self.assertDriverContainsText('body', 'TC AD')

        report_result_signals = seller_server.get_first_request("/reportResult").get_first_json_param('signals')
        logger.info(f"reportResult() signals: {pretty_json(report_result_signals)}")

        report_win_signals = buyer_server.get_first_request("/reportWin").get_first_json_param('signals')
        logger.info(f"reportWin() signals: {pretty_json(report_win_signals)}")

        # to be able to measure bidding worklet time you should use custom-built version of chromium
        # with a patch like this: https://github.com/RTBHOUSE/chromium/commits/auction_timer
        if 'bid_duration' in report_result_signals.get('browserSignals'):
            bid_duration_ms = int(report_result_signals.get('browserSignals').get('bid_duration')) / 1000
            logger.info(f"generateBid took: {bid_duration_ms} ms")
