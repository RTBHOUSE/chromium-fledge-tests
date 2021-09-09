# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import json
import logging
import threading
import time
from datetime import datetime
from functools import wraps

from common.config import config

logger = logging.getLogger(__file__)


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
        with TrackFile(config.get('service_log_path')):
            return method(self, *args, **kwargs)
    return inner_print_debug


def pretty_json(data):
    return json.dumps(data, indent=2, sort_keys=True)