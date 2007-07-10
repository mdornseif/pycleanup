#!/usr/bin/env python2.5
"""Tests that run all fixer modules over an input stream.

This has been broken out into its own test module because of its
running time.
"""
# Author: Collin Winter

# Testing imports
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

class Test_all(support.TestCase):
    def setUp(self):
        options = Options(fix=["all"], print_function=False)
        self.refactor = refactor.RefactoringTool(options)

    def refactor_stream(self, stream_name, stream):
        try:
            tree = self.refactor.driver.parse_stream(stream)
        except Exception, err:
            raise
        self.refactor.refactor_tree(tree, stream_name)
        return str(tree)

    def test_examples_file(self):
        # Just test that we can parse examples.py without failing
        basedir = os.path.dirname(refactor.__file__)
        example = os.path.join(basedir, "example.py")
        self.refactor_stream("example.py", open(example))

    def test_fixers(self):
        # Just test that we can parse all the fixers without failing
        basedir = os.path.dirname(refactor.__file__)
        fixerdir = os.path.join(basedir, "fixes")
        for filename in os.listdir(fixerdir):
            if not filename.endswith(".py"):
                continue
            print "Fixing %s..." % filename
            fixer = os.path.join(fixerdir, filename)
            self.refactor_stream(fixer, open(fixer))


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
