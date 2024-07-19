# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import json
import logging
import os
import pathlib
import random
import shutil
import sys
import unittest
import warnings

from selenium import webdriver
from selenium.webdriver.chrome import service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


logger = logging.getLogger(__file__)

ROOT_DIR = pathlib.Path(__file__).absolute().parent.parent.parent

CHROMIUM_DIR = os.environ.get('CHROMIUM_DIR') or (str(ROOT_DIR / "_chromium")
                                                  if (ROOT_DIR / "_chromium").exists() else None)
PROFILE_DIR = os.environ.get('PROFILE_DIR') or str(ROOT_DIR / "profile")
CHROMEDRIVER_LOG_PATH = os.environ.get('CHROMEDRIVER_LOG_PATH') or str(ROOT_DIR / "chromedriver.log")

NSSDB_DIR = str(pathlib.Path(__file__).absolute().parent / "ssl" / "ca" / "nssdb")

CHROME_HEADLESS = os.environ.get('CHROME_HEADLESS', '0').lower() not in ['0', 'false']

PRIVACY_SANDBOX_ENROLLMENT_OVERRIDES = ['https://localhost']

class ComponentNotFoundException(Exception):
    pass

class BaseTest(unittest.TestCase):

    def non_feature_options(self) -> webdriver.ChromeOptions:
        # https://peter.sh/experiments/chromium-command-line-switches
        options = webdriver.ChromeOptions()
        if CHROMIUM_DIR:
            options.binary_location = CHROMIUM_DIR + '/chrome'
        options.set_capability('goog:loggingPrefs', dict(browser='ALL', performance='ALL'))
        options.add_experimental_option('perfLoggingPrefs', dict(traceCategories='fledge'))
        options.add_argument('--enable-stats-collection-bindings')  # for histograms
        options.add_argument('--no-sandbox')
        options.add_argument('--no-zygote')
        if CHROME_HEADLESS:
            options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-data-dir={PROFILE_DIR}')
        options.add_argument('--disable-features=ChromeWhatsNewUI')
        options.add_argument(f'--privacy-sandbox-enrollment-overrides={",".join(PRIVACY_SANDBOX_ENROLLMENT_OVERRIDES)}')
        return options

    def options(self) -> webdriver.ChromeOptions:
        options = self.non_feature_options()
        enabled_features = [
            'InterestGroupStorage',
            'AllowURNsInIframes',  # FOT#1
            'FencedFrames:implementation_type/mparch',
            'BiddingAndScoringDebugReportingAPI',
            'PrivacySandboxAdsAPIsOverride',
            'OverridePrivacySandboxSettingsLocalTesting',
            'PrivacySandboxAttestationsHigherComponentRegistrationPriority',
        ]
        options.add_argument(f"--enable-features={','.join(enabled_features)}")
        return options

    def setUp(self) -> None:
        # initialize the random number generator with the current system time
        random.seed()

        if os.path.exists(PROFILE_DIR):
            shutil.rmtree(PROFILE_DIR)

        chrome_home_dir = PROFILE_DIR
        os.makedirs(chrome_home_dir + "/.pki")
        os.symlink(NSSDB_DIR, chrome_home_dir + "/.pki/nssdb")

        warnings.filterwarnings("ignore")
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
        driver = webdriver.Chrome(
            service=service.Service(
                CHROMIUM_DIR + '/chromedriver' if CHROMIUM_DIR else 'chromedriver',
                service_args=['--enable-chrome-logs'],
                log_path=CHROMEDRIVER_LOG_PATH,
                env=dict(os.environ, HOME=chrome_home_dir)
            ),
            options=self.options()
        )
        self.driver = driver
        self.saved_wd = os.getcwd()
        os.chdir(os.path.dirname(sys.modules[self.__module__].__file__))

    def tearDown(self) -> None:
        os.chdir(self.saved_wd)
        self.driver.quit()
        if os.path.exists(PROFILE_DIR):
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

    def updatePrivacySandboxAttestationsComponent(self, **kwargs):
        """
        Update a privacy sandbox attestations component. Meant to be used in e2e tests that should use real world
        settings and using --override-sandbox-enrollment-overrides is not desirable.
        """
        self.updateComponent('Privacy Sandbox Attestations', **kwargs)

    def updateComponent(self, component_name, timeout=30):
        self.driver.get('chrome://components')
        components_by_name = {
            component.find_element(By.XPATH, './/span[@class="component-name"]').text: component
            for component in self.driver.find_elements(By.XPATH, '//div[@class="component"]')
        }

        component = components_by_name.get(component_name)
        if component is None:
            raise ComponentNotFoundException(component_name)

        component = components_by_name[component_name]
        component.find_element(By.XPATH, './/button').click()

        def component_updated(_):
            status = component.find_element(By.XPATH, './/span[@jscontent="status"]').text
            return status in {'Component updated', 'Component already up to date'}

        WebDriverWait(self.driver, timeout).until(component_updated)

    def extract_browser_log(self):
        return self.driver.get_log('browser')

    def extract_trace_events(self):
        trace_events = []
        for entry in self.driver.get_log('performance'):
            data = json.loads(entry['message'])
            if data.get('message', {}).get('method') == 'Tracing.dataCollected':
                trace_events.append(data['message']['params'])
        return trace_events

    def extract_browser_histogram(self, histogram, timeout=5):
        js = 'return statsCollectionController.getBrowserHistogram("%s")' % histogram

        return WebDriverWait(self.driver, timeout) \
            .until(lambda driver: json.loads(driver.execute_script(js)))

    def extract_fledge_trace_events(self):
        fledge_events = [x for x in self.extract_trace_events() if 'fledge' == x.get('cat', None)]
        fledge_events.sort(key=lambda x: x['ts'])
        return fledge_events
