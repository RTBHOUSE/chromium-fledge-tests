# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import MeasureDuration
from common.utils import log_exception
from common.utils import measure_time
from common.utils import print_debug

logger = logging.getLogger(__file__)


class IframeTest(BaseTest):

    @print_debug
    @measure_time
    @log_exception
    def test__should_show_ad_jeff_through_iframe(self):
        with MockServer(port=8111, directory='resources/buyer') as buyer_server:

            with MeasureDuration("joinAdInterestGroup"):
                self.driver.get(buyer_server.address)
                self.findFrameAndSwitchToIt()
                self.assertDriverContainsText('body', 'joined interest group')

            with MeasureDuration("runAdAuction"):
                self.driver.get('https://www.jefftk.com/test/td/auction.html')
                self.driver.find_element(By.TAG_NAME, 'button').click()
                self.findFrameAndSwitchToIt()
                self.assertDriverContainsText('body', 'TC AD 1')
