"""Support code for test_*.py files"""
# Author: Collin Winter

import unittest
import sys
import os.path
import re

TestCase = unittest.TestCase

def run_all_tests(test_mod=None, tests=None):
    if tests is None:
        tests = unittest.TestLoader().loadTestsFromModule(test_mod)
    unittest.TextTestRunner(verbosity=2).run(tests)


def adjust_path():
    parent_dir = os.path.split(sys.path[0])[0]
    sys.path = [parent_dir] + sys.path


skip_whitespace = re.compile(r"""\S""")
def reformat(string):
    indent = re.search(skip_whitespace, string).start()
    if indent == 0:
        code = string
    else:
        code = "\n".join(line[indent-1:] for line in string.split("\n")[1:])
    return code + "\n\n"
