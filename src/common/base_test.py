# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
import logging
import os
import shutil
import unittest
import warnings

import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.config import config

logger = logging.getLogger(__file__)

PROFILE_DIR = '/tmp/profile123'

class BaseTest(unittest.TestCase):

    def non_feature_options(self) -> webdriver.ChromeOptions:
        # https://peter.sh/experiments/chromium-command-line-switches
        options = webdriver.ChromeOptions()
        options.binary_location = '/home/usertd/chromium/chrome'
        # FIXME headless chrome does not work with fledge, https://bugs.chromium.org/p/chromium/issues/detail?id=1229652
        # options.headless = True
        options.set_capability('goog:loggingPrefs', dict(browser='ALL', performance='ALL'))
        options.add_experimental_option('perfLoggingPrefs', dict(traceCategories='fledge'))
        options.add_argument('--no-sandbox')
        options.add_argument('--no-zygote')
        # FIXME headless chrome does not work with fledge, https://bugs.chromium.org/p/chromium/issues/detail?id=1229652
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-data-dir={PROFILE_DIR}')
        options.add_argument('--disable-features=ChromeWhatsNewUI')
        return options

    def options(self) -> webdriver.ChromeOptions:
        options = self.non_feature_options()
        enabled_features = [
            'InterestGroupStorage',
            'AllowURNsInIframes', # FOT#1
            'FencedFrames:implementation_type/mparch',
            'BiddingAndScoringDebugReportingAPI',
            'PrivacySandboxAdsAPIsOverride',
            'OverridePrivacySandboxSettingsLocalTesting'
        ]
        options.add_argument(f"--enable-features={','.join(enabled_features)}")
        return options

    def setUp(self) -> None:
        warnings.filterwarnings("ignore")
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
        driver = webdriver.Chrome('/home/usertd/chromium/chromedriver', options=self.options(),
                                  service_args=['--enable-chrome-logs'],
                                  service_log_path=config.get('service_log_path'))
        self.driver = driver
        self.saved_wd = os.getcwd()
        os.chdir(os.path.dirname(sys.modules[self.__module__].__file__))

        # Workaround for 'target frame attached'
        # https://bugs.chromium.org/p/chromedriver/issues/detail?id=4048
        # https://groups.google.com/g/chromedriver-users/c/Z_CaHJTJnLw
        buggyDriverExecute = self.driver.execute
        def suppressingDriverExecute(*args, **kwargs):
            while True:
                try:
                    return buggyDriverExecute(*args, **kwargs)
                except Exception as e:
                    if 'target frame detached' not in str(e):
                        raise
                    logger.warning("Supressing 'target frame detached'", exc_info=True)
        self.driver.execute = suppressingDriverExecute

    def tearDown(self) -> None:
        os.chdir(self.saved_wd)
        self.driver.quit()
        shutil.rmtree(PROFILE_DIR)

    def assertDriverContainsText(self, css_selector, text, timeout=5):
        exc_msg = f'Failed to find text "{text}" in element "{css_selector}" ' \
                  f'in given time {timeout} seconds.'
        WebDriverWait(self.driver, timeout) \
            .until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, css_selector), text), exc_msg)

    def findFrameAndSwitchToIt(self, timeout=5):
        exc_msg = f'Failed to find frame in given time {timeout} seconds.'
        frame = WebDriverWait(self.driver, timeout) \
            .until(EC.presence_of_element_located((By.XPATH, '//iframe|//fencedframe')), exc_msg)
        logger.info(f"{frame.tag_name}.src: {frame.get_attribute('src')}")
        self.driver.switch_to.frame(frame)

    def extract_trace_events(self):
        trace_events = []
        for entry in self.driver.get_log('performance'):
            data = json.loads(entry['message'])
            if data.get('message', {}).get('method') == 'Tracing.dataCollected':
                trace_events.append(data['message']['params'])
        return trace_events
