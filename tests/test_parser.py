#!/usr/bin/env python2.5
"""Test suite for 2to3's parser."""
# Author: Collin Winter

# Testing imports
import support
from support import driver, test_dir

# Python imports
import os
import os.path

# Local imports
from pgen2.parse import ParseError


class TestParserIdempotency(support.TestCase):

    """A cut-down version of pytree_idempotency.py."""

    def test_all_project_files(self):
        for filepath in support.all_project_files():
            print "Parsing %s..." % filepath
            tree = driver.parse_file(filepath, debug=True)
            if diff(filepath, tree):
                self.fail("Idempotency failed: %s" % filepath)


def diff(fn, tree):
    f = open("@", "w")
    try:
        f.write(str(tree))
    finally:
        f.close()
    try:
        return os.system("diff -u %s @" % fn)
    finally:
        os.remove("@")


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
