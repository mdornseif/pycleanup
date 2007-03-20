"""Support code for test_*.py files"""
# Author: Collin Winter

import unittest
import sys
import os.path
import re
from textwrap import dedent

TestCase = unittest.TestCase

# Python 2.3's TestSuite is not iter()-able
if sys.version_info < (2, 4):
    def TestSuite_iter(self):
        return iter(self._tests)
    unittest.TestSuite.__iter__ = TestSuite_iter

def run_all_tests(test_mod=None, tests=None):
    if tests is None:
        tests = unittest.TestLoader().loadTestsFromModule(test_mod)
    unittest.TextTestRunner(verbosity=2).run(tests)


def adjust_path():
    parent_dir = os.path.split(sys.path[0])[0]
    sys.path = [parent_dir] + sys.path

def reformat(string):
    return dedent(string) + "\n\n"
