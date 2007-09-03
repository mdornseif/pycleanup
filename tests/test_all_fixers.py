#!/usr/bin/env python2.5
"""Tests that run all fixer modules over an input stream.

This has been broken out into its own test module because of its
running time.
"""
# Author: Collin Winter

# Testing imports
try:
    from tests import support
except ImportError:
    import support

# Python imports
from StringIO import StringIO
import logging
import os
import os.path
import unittest

# Local imports
import pytree
import refactor

class Options:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.verbose = False
        self.doctests_only = False

class Test_all(support.TestCase):
    def setUp(self):
        options = Options(fix=["all"], write=False)
        self.refactor = refactor.RefactoringTool(options)

    def test_all_project_files(self):
        for filepath in support.all_project_files():
            print "Fixing %s..." % filepath
            self.refactor.refactor_file(filepath)


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
