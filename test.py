#!/usr/bin/env python2.5

"""Main test file for 2to3.

Running "python test.py" will run all tests in tests/test_*.py.
"""
# Author: Collin Winter

import tests
import tests.support

tests.support.run_all_tests(tests=tests.all_tests)
