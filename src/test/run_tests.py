import logging
import sys
import unittest


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    tests = unittest.TestLoader().discover('.', 'test*.py')
    unittest.TextTestRunner(verbosity=2).run(tests)
