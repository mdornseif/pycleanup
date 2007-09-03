#!/usr/bin/env python2.5
""" Test suite for refactor.py """
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
import refactor


class Options:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.verbose = False
        self.doctests_only = False


class TestAutomaticPrintDetection(unittest.TestCase):

    def setUp(self):
        self.refactor = refactor.RefactoringTool(Options(fix=["print"]))

    def _check(self, before, after):
        before = support.reformat(before)
        after = support.reformat(after)
        tree = self.refactor.refactor_string(before, "<stream>")
        self.failUnlessEqual(str(tree), after)
        return tree

    def check(self, before, after):
        tree = self._check(before, after)
        self.failUnless(tree.was_changed)

    def unchanged(self, before):
        tree = self._check(before, before)
        self.failIf(tree.was_changed)

    def test_print_statement(self):
        b = """print >>b, c"""
        a = """print(c, file=b)"""
        self.check(b, a)

    def test_print_function(self):
        s = """print(c, file=b)"""
        self.unchanged(s)


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
