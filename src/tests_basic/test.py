# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.utils import print_debug
from common.utils import log_exception
from common.mockserver import MockServer
from common.base_test import BaseTest

logger = logging.getLogger(__file__)


class BasicTest(BaseTest):

    def test__driver_should_work(self):
        self.driver.get('https://techblog.rtbhouse.com/')
        self.assertDriverContainsText('#bs-example-navbar-collapse-1 > ul', 'HOME')

    @print_debug
    @log_exception
    def test__should_report_win(self):
        with MockServer(8081, '/home/usertd/tests/tests_basic/resources/buyer') as buyer_server,\
                MockServer(8082, '/home/usertd/tests/tests_basic/resources/publisher') as publisher_server,\
                MockServer(8083, '/home/usertd/tests/tests_basic/resources/seller') as seller_server:

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
