# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import log_exception
from common.utils import measure_time
from common.utils import print_debug

logger = logging.getLogger(__file__)


class DailyUpdateTest(BaseTest):

    @print_debug
    @measure_time
    @log_exception
    def test__should_update(self):
        with MockServer(8201, '/home/usertd/tests/tests_daily_update/resources/buyer') as buyer_server,\
                MockServer(8202, '/home/usertd/tests/tests_daily_update/resources/seller') as seller_server:

            # join interest group
            self.driver.get(buyer_server.address)
            self.assertDriverContainsText('body', 'joined interest group')

            # run auction
            self.driver.get(seller_server.address)
            WebDriverWait(self.driver, 5)\
                .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
            self.assertDriverContainsText('body', 'TC AD 1')

            # update interest group
            self.driver.get(buyer_server.address + "/do_update.html")
            self.assertDriverContainsText('body', 'updated interest group')

            # wait for the browser to download updates
            time.sleep(5)

            # run auction again to check if the update was successful
            # (note that now we expect a different ad to win)
            self.driver.get(seller_server.address)
            WebDriverWait(self.driver, 5) \
                .until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe')))
            self.assertDriverContainsText('body', 'TC AD 2')
