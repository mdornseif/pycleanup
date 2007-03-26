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


def parse(code, strip_levels=0):
    # The topmost node is file_input, which we don't care about.
    # The next-topmost node is a *_stmt node, which we also don't care about
    tree = support.parse_string(code)
    for i in range(strip_levels):
        tree = tree.children[0]
    tree.parent = None
    return tree
    
class MacroTestCase(support.TestCase):
    def assertStr(self, node, string):
        if isinstance(node, (tuple, list)):
            node = pytree.Node(util.syms.simple_stmt, node)
        self.assertEqual(str(node), string)


class Test_is_tuple(support.TestCase):
    def is_tuple(self, string):
        return util.is_tuple(parse(string, strip_levels=2))

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
        return util.is_list(parse(string, strip_levels=2))

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
        call = parse("foo()", strip_levels=2)
    
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
        

class Test_find_binding(support.TestCase):
    def find_binding(self, name, string):
        return util.find_binding(name, parse(string))

    def test_simple_assignment(self):
        self.failUnless(self.find_binding("a", "a = b"))
        self.failUnless(self.find_binding("a", "a = [b, c, d]"))
        self.failUnless(self.find_binding("a", "a = foo()"))
        self.failUnless(self.find_binding("a", "a = foo().foo.foo[6][foo]"))
        self.failIf(self.find_binding("a", "foo = a"))
        self.failIf(self.find_binding("a", "foo = (a, b, c)"))

    def test_tuple_assignment(self):
        self.failUnless(self.find_binding("a", "(a,) = b"))
        self.failUnless(self.find_binding("a", "(a, b, c) = [b, c, d]"))
        self.failUnless(self.find_binding("a", "(c, (d, a), b) = foo()"))
        self.failUnless(self.find_binding("a", "(a, b) = foo().foo.foo[6][foo]"))
        self.failIf(self.find_binding("a", "(foo, b) = (b, a)"))
        self.failIf(self.find_binding("a", "(foo, b, c) = (a, b, c)"))

    def test_list_assignment(self):
        self.failUnless(self.find_binding("a", "[a] = b"))
        self.failUnless(self.find_binding("a", "[a, b, c] = [b, c, d]"))
        self.failUnless(self.find_binding("a", "[c, [d, a], b] = foo()"))
        self.failUnless(self.find_binding("a", "[a, b] = foo().foo.foo[a][foo]"))
        self.failIf(self.find_binding("a", "[foo, b] = (b, a)"))
        self.failIf(self.find_binding("a", "[foo, b, c] = (a, b, c)"))
        
    def test_invalid_assignments(self):
        self.failIf(self.find_binding("a", "foo.a = 5"))
        self.failIf(self.find_binding("a", "foo[a] = 5"))
        self.failIf(self.find_binding("a", "foo(a) = 5"))
        self.failIf(self.find_binding("a", "foo(a, b) = 5"))
        
    def test_simple_import(self):
        self.failUnless(self.find_binding("a", "import a"))
        self.failUnless(self.find_binding("a", "import b, c, a, d"))
        self.failIf(self.find_binding("a", "import b"))
        self.failIf(self.find_binding("a", "import b, c, d"))
        
    def test_from_import(self):
        self.failUnless(self.find_binding("a", "from x import a"))
        self.failUnless(self.find_binding("a", "from a import a"))
        self.failUnless(self.find_binding("a", "from x import b, c, a, d"))
        self.failUnless(self.find_binding("a", "from x.b import a"))
        self.failUnless(self.find_binding("a", "from x.b import b, c, a, d"))
        self.failIf(self.find_binding("a", "from a import b"))
        self.failIf(self.find_binding("a", "from a.d import b"))
        self.failIf(self.find_binding("a", "from d.a import b"))
        
    def test_import_as(self):
        self.failUnless(self.find_binding("a", "import b as a"))
        self.failUnless(self.find_binding("a", "import b as a, c, a as f, d"))
        self.failIf(self.find_binding("a", "import a as f"))
        self.failIf(self.find_binding("a", "import b, c as f, d as e"))
        
    def test_from_import_as(self):
        self.failUnless(self.find_binding("a", "from x import b as a"))
        self.failUnless(self.find_binding("a", "from x import g as a, d as b"))
        self.failUnless(self.find_binding("a", "from x.b import t as a"))
        self.failUnless(self.find_binding("a", "from x.b import g as a, d"))
        self.failIf(self.find_binding("a", "from a import b as t"))
        self.failIf(self.find_binding("a", "from a.d import b as t"))
        self.failIf(self.find_binding("a", "from d.a import b as t"))
        
    def test_function_def(self):
        self.failUnless(self.find_binding("a", "def a(): pass"))
        self.failUnless(self.find_binding("a", "def a(b, c, d): pass"))
        self.failUnless(self.find_binding("a", "def a(): b = 7"))
        self.failIf(self.find_binding("a", "def d(b, (c, a), e): pass"))
        self.failIf(self.find_binding("a", "def d(a=7): pass"))
        self.failIf(self.find_binding("a", "def d(a): pass"))
        self.failIf(self.find_binding("a", "def d(): a = 7"))
        
    def test_class_def(self):
        self.failUnless(self.find_binding("a", "class a: pass"))
        self.failUnless(self.find_binding("a", "class a(): pass"))
        self.failUnless(self.find_binding("a", "class a(b): pass"))
        self.failUnless(self.find_binding("a", "class a(b, c=8): pass"))
        self.failIf(self.find_binding("a", "class d: pass"))
        self.failIf(self.find_binding("a", "class d(a): pass"))
        self.failIf(self.find_binding("a", "class d(b, a=7): pass"))
        self.failIf(self.find_binding("a", "class d(b, *a): pass"))
        self.failIf(self.find_binding("a", "class d(b, **a): pass"))
        self.failIf(self.find_binding("a", "class d: a = 7"))
        
    def test_for(self):
        self.failUnless(self.find_binding("a", "for a in r: pass"))
        self.failUnless(self.find_binding("a", "for a, b in r: pass"))
        self.failUnless(self.find_binding("a", "for (a, b) in r: pass"))
        self.failUnless(self.find_binding("a", "for c, (a,) in r: pass"))
        self.failUnless(self.find_binding("a", "for c, (a, b) in r: pass"))
        self.failUnless(self.find_binding("a", "for c in r: a = c"))
        

if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
