#!/usr/bin/env python2.5

"""Main test file for 2to3.

Running "python test.py" will run all tests in tests/test_*.py.
"""
# Author: Collin Winter

from lib2to3 import tests
import lib2to3.tests.support

tests.support.run_all_tests(tests=tests.all_tests)
