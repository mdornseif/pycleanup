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

def parse(code):
    # The topmost node is file_input, which we don't care about.
    # The next-topmost node is a *_stmt node, which we also don't care about
    tree = support.parse_string(code)
    node = tree.children[0].children[0]
    node.parent = None
    return node
    
class MacroTestCase(support.TestCase):
    def assertStr(self, node, string):
        if isinstance(node, (tuple, list)):
            node = pytree.Node(util.syms.simple_stmt, node)
        self.assertEqual(str(node), string)


class Test_is_tuple(support.TestCase):
    def is_tuple(self, string):
        return util.is_tuple(parse(string))

    def test_valid(self):
        self.failUnless(self.is_tuple("(a, b)"))
        self.failUnless(self.is_tuple("(a, (b, c))"))
        self.failUnless(self.is_tuple("((a, (b, c)),)"))
        self.failUnless(self.is_tuple("(a,)"))
    
    def test_invalid(self):
        self.failIf(self.is_tuple("(a)"))
        self.failIf(self.is_tuple("('foo') % (b, c)"))


class Test_is_list(support.TestCase):
    def is_list(self, string):
        return util.is_list(parse(string))

    def test_valid(self):
        self.failUnless(self.is_list("[]"))
        self.failUnless(self.is_list("[a]"))
        self.failUnless(self.is_list("[a, b]"))
        self.failUnless(self.is_list("[a, [b, c]]"))
        self.failUnless(self.is_list("[[a, [b, c]],]"))
        
    def test_invalid(self):
        self.failIf(self.is_list("[]+[]"))


class Test_Attr(MacroTestCase):
    def test(self):
        from fixes.util import Attr, Name
        call = parse("foo()")
    
        self.assertStr(Attr(Name("a"), Name("b")), "a.b")
        self.assertStr(Attr(call, Name("b")), "foo().b")
        
    def test_returns(self):
        from fixes.util import Attr, Name
        
        attr = Attr(Name("a"), Name("b"))
        self.assertEqual(type(attr), tuple)

        
class Test_Name(MacroTestCase):
    def test(self):
        from fixes.util import Name
        
        self.assertStr(Name("a"), "a")
        self.assertStr(Name("foo.foo().bar"), "foo.foo().bar")
        self.assertStr(Name("a", prefix="b"), "ba")


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
