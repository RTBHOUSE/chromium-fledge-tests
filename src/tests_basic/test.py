# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import logging

from common.base_test import BaseTest
from common.mockserver import MockServer
from common.utils import log_exception
from common.utils import print_debug

logger = logging.getLogger(__file__)


class BasicTest(BaseTest):

    def test__driver_should_work(self):
        self.driver.get('https://techblog.rtbhouse.com/')
        self.assertDriverContainsText('#bs-example-navbar-collapse-1 > ul', 'HOME')

    @print_debug
    @log_exception
    def test__should_report_win(self):
        with MockServer(port=8081, directory='resources/buyer') as buyer_server, \
                MockServer(port=8082, directory='resources/publisher') as publisher_server, \
                MockServer(port=8083, directory='resources/seller') as seller_server:
            self.driver.get(buyer_server.address)
            self.assertDriverContainsText('h1', 'Hello')
            self.driver.get(publisher_server.address)
