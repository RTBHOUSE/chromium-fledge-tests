from common.base_test import BaseTest
from common.utils import print_debug, measure_time, log_exception


class FunctionalTest(BaseTest):

    @print_debug
    @measure_time
    @log_exception
    def test__basic_webassembly(self):
        self.fail("To instantiate WebAssembly async-functions must be supported.")
        pass
