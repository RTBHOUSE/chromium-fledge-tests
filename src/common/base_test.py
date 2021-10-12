# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import sys
import logging
import os
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.config import config

logger = logging.getLogger(__file__)


class BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
        # https://peter.sh/experiments/chromium-command-line-switches
        options = webdriver.ChromeOptions()
        if os.path.isdir('/home/usertd/chromium-custom/'):
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
        # ver <= 96.x
        # options.add_argument('--enable-features=FledgeInterestGroups,FledgeInterestGroupAPI')
        # ver >= 97.x
        options.add_argument('--enable-features=InterestGroupStorage,AdInterestGroupAPI,Fledge')
        # TODO: at some point in the future FLEDGE won't work with disabled FencedFrames
        options.add_argument('--disable-features=FencedFrames')
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['goog:loggingPrefs'] =  { 'browser':'ALL' }
        driver = webdriver.Chrome('/home/usertd/chromedriver_linux64/chromedriver', options=options,
                                  desired_capabilities=desired_capabilities,
                                  service_args=['--enable-chrome-logs'],
                                  service_log_path=config.get('service_log_path'))
        self.driver = driver
        self.saved_wd = os.getcwd()
        os.chdir(os.path.dirname(sys.modules[self.__module__].__file__))

    def tearDown(self) -> None:
        os.chdir(self.saved_wd)
        self.driver.quit()

    def assertDriverContainsText(self, css_selector, text, timeout=5):
        exc_msg = f'Failed to find text "{text}" in element "{css_selector}" '\
                  f'in given time {timeout} seconds.'
        WebDriverWait(self.driver, timeout)\
            .until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, css_selector), text), exc_msg)
