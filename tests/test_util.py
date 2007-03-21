#!/usr/bin/env python2.5
""" Test suite for the code in fixes.util """
# Author: Collin Winter

# Testing imports
import support

# Python imports
import os.path

# Local imports
import pytree
from fixes import util
from pgen2 import driver
from pgen2.parse import ParseError

test_dir = os.path.dirname(__file__)
grammar_path = os.path.join(test_dir, "..", "Grammar.txt")
grammar = driver.load_grammar(grammar_path)
driver = driver.Driver(grammar, convert=pytree.convert)

def parse(code):
    # The topmost node is file_input, which we don't care about.
    # The next-topmost node is a *_stmt node, which we also don't care about
    tree = driver.parse_string(support.reformat(code), debug=True)
    return tree.children[0].children[0]

class Test_is_tuple(support.TestCase):
    def test_valid(self):
        self.failUnless(util.is_tuple(parse("(a, b)")))
        self.failUnless(util.is_tuple(parse("(a, (b, c))")))
        self.failUnless(util.is_tuple(parse("((a, (b, c)),)")))
        self.failUnless(util.is_tuple(parse("(a,)")))
    
    def test_invalid(self):
        self.failIf(util.is_tuple(parse("(a)")))
        self.failIf(util.is_tuple(parse("('foo') % (b, c)")))

class Test_is_list(support.TestCase):
    def test_valid(self):
        self.failUnless(util.is_list(parse("[]")))
        self.failUnless(util.is_list(parse("[a]")))
        self.failUnless(util.is_list(parse("[a, b]")))
        self.failUnless(util.is_list(parse("[a, [b, c]]")))
        self.failUnless(util.is_list(parse("[[a, [b, c]],]")))
        
    def test_invalid(self):
        self.failIf(util.is_list(parse("[]+[]")))


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
