# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import json
import logging
import os
import statistics
import threading
import time
from collections import defaultdict
from datetime import datetime
from functools import wraps
from typing import Any, Dict

from common.base_test import CHROMEDRIVER_LOG_PATH

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


class AverageBenchmarks:
    MEAN = "mean"
    MEDIAN = "median"
    AVERAGE_FUN = {
        MEAN: statistics.mean,
        MEDIAN: statistics.median,
    }

    def __init__(self, method, method_self, *args, **kwargs):
        self.method = method
        self.method_self = method_self
        self.args = args
        self.kwargs = kwargs
        self.results = defaultdict(list)

    def run(self, times: int):
        for _ in range(times):
            one_run_results = self.method(self.method_self, *self.args, **self.kwargs)
            for k, f in one_run_results.items():
                self.results[k].append(f)

    def log_averaged_results(self, mode: str = MEDIAN):
        avg_fun = AverageBenchmarks.AVERAGE_FUN[mode]
        logger.info(f"{self.method.__name__} benchmarks ({mode})")
        for k, lst in self.results.items():
            av = avg_fun(lst)
            logger.info(f"  - {k}: {av}      {lst}")


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
            for entry in self.driver.get_log('browser'):
                logger.warning(entry)
            raise

    return inner_log_exception


def print_debug(method):
    @wraps(method)
    def inner_print_debug(self, *args, **kwargs):
        with TrackFile(CHROMEDRIVER_LOG_PATH):
            return method(self, *args, **kwargs)

    return inner_print_debug


def pretty_json(data):
    return json.dumps(data, indent=2, sort_keys=True)


def extract_rtbh_test_stats(signals: Dict[str, Any]) -> Dict[str, float]:
    try:
        results = {}
        one_run_results = json.loads(signals['browserSignals']['rtbh_test_stats'])
        for k, v in one_run_results.items():
            try:
                results[k + '_ms'] = float(v) / 1000
            except ValueError:
                pass

        return results
    except KeyError:
        # If we set AVERAGE_BENCHMARKS_TIMES we apparently wanted to get measurements,
        # so without them we can't do anything reasonable and just raise an exception.
        # Otherwise, we don't care about the test statistcs and simply return an empty dictionary.
        if 'AVERAGE_BENCHMARKS_TIMES' in os.environ:
            raise RuntimeError("No test statistics in browser singals.")
        return {}


def average_benchmarks(method):
    @wraps(method)
    def inner_average_benchmarks(self, *args, **kwargs):
        ab = AverageBenchmarks(method, self, *args, **kwargs)
        ab.run(times=int(os.environ.get('AVERAGE_BENCHMARKS_TIMES', '1')))
        ab.log_averaged_results()

    return inner_average_benchmarks
