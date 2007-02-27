"""Make tests/ into a package. This allows us to "import tests" and
have tests.all_tests be a TestSuite representing all test cases
from all test_*.py files in tests/."""
# Author: Collin Winter

import os
import os.path
import unittest
import types

import support

all_tests = unittest.TestSuite()

tests_dir = os.path.join(os.getcwd(), 'tests')
tests = [t[0:-3] for t in os.listdir(tests_dir)
                        if t.startswith('test_') and t.endswith('.py')]

loader = unittest.TestLoader()
for t in tests:
    __import__('tests.' + t)
    mod = globals()[t]
    all_tests.addTests(loader.loadTestsFromModule(mod))
