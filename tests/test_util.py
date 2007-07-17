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
        self.failUnless(self.is_tuple("()"))
    
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
        self.assertEqual(type(attr), list)

        
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
        self.failIf(self.find_binding("a", "(foo, (b, c)) = (a, b, c)"))

    def test_list_assignment(self):
        self.failUnless(self.find_binding("a", "[a] = b"))
        self.failUnless(self.find_binding("a", "[a, b, c] = [b, c, d]"))
        self.failUnless(self.find_binding("a", "[c, [d, a], b] = foo()"))
        self.failUnless(self.find_binding("a", "[a, b] = foo().foo.foo[a][foo]"))
        self.failIf(self.find_binding("a", "[foo, b] = (b, a)"))
        self.failIf(self.find_binding("a", "[foo, [b, c]] = (a, b, c)"))
        
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
        
        s = """
            def d():
                def a():
                    pass"""
        self.failIf(self.find_binding("a", s))
        
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
        
        s = """
            class d():
                class a():
                    pass"""
        self.failIf(self.find_binding("a", s))
        
    def test_for(self):
        self.failUnless(self.find_binding("a", "for a in r: pass"))
        self.failUnless(self.find_binding("a", "for a, b in r: pass"))
        self.failUnless(self.find_binding("a", "for (a, b) in r: pass"))
        self.failUnless(self.find_binding("a", "for c, (a,) in r: pass"))
        self.failUnless(self.find_binding("a", "for c, (a, b) in r: pass"))
        self.failUnless(self.find_binding("a", "for c in r: a = c"))
        self.failIf(self.find_binding("a", "for c in a: pass"))
        
    def test_for_nested(self):
        s = """
            for b in r:
                for a in b:
                    pass"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            for b in r:
                for a, c in b:
                    pass"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            for b in r:
                for (a, c) in b:
                    pass"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            for b in r:
                for (a,) in b:
                    pass"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            for b in r:
                for c, (a, d) in b:
                    pass"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            for b in r:
                for c in b:
                    a = 7"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            for b in r:
                for c in b:
                    d = a"""
        self.failIf(self.find_binding("a", s))
        
        s = """
            for b in r:
                for c in a:
                    d = 7"""
        self.failIf(self.find_binding("a", s))
        
    def test_if(self):
        self.failUnless(self.find_binding("a", "if b in r: a = c"))
        self.failIf(self.find_binding("a", "if a in r: d = e"))
    
    def test_if_nested(self):
        s = """
            if b in r:
                if c in d:
                    a = c"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            if b in r:
                if c in d:
                    c = a"""
        self.failIf(self.find_binding("a", s))
        
    def test_while(self):
        self.failUnless(self.find_binding("a", "while b in r: a = c"))
        self.failIf(self.find_binding("a", "while a in r: d = e"))
    
    def test_while_nested(self):
        s = """
            while b in r:
                while c in d:
                    a = c"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            while b in r:
                while c in d:
                    c = a"""
        self.failIf(self.find_binding("a", s))
        
    def test_try_except(self):
        s = """
            try:
                a = 6
            except:
                b = 8"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            except:
                a = 6"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            except KeyError:
                pass
            except:
                a = 6"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            except:
                b = 6"""
        self.failIf(self.find_binding("a", s))
        
    def test_try_except_nested(self):
        s = """
            try:
                try:
                    a = 6
                except:
                    pass
            except:
                b = 8"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            except:
                try:
                    a = 6
                except:
                    pass"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            except:
                try:
                    pass
                except:
                    a = 6"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                try:
                    b = 8
                except KeyError:
                    pass
                except:
                    a = 6
            except:
                pass"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                pass
            except:
                try:
                    b = 8
                except KeyError:
                    pass
                except:
                    a = 6"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            except:
                b = 6"""
        self.failIf(self.find_binding("a", s))
        
        s = """
            try:
                try:
                    b = 8
                except:
                    c = d
            except:
                try:
                    b = 6
                except:
                    t = 8
                except:
                    o = y"""
        self.failIf(self.find_binding("a", s))
        
    def test_try_except_finally(self):
        s = """
            try:
                c = 6
            except:
                b = 8
            finally:
                a = 9"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            finally:
                a = 6"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            finally:
                b = 6"""
        self.failIf(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            except:
                b = 9
            finally:
                b = 6"""
        self.failIf(self.find_binding("a", s))
        
    def test_try_except_finally_nested(self):
        s = """
            try:
                c = 6
            except:
                b = 8
            finally:
                try:
                    a = 9
                except:
                    b = 9
                finally:
                    c = 9"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            finally:
                try:
                    pass
                finally:
                    a = 6"""
        self.failUnless(self.find_binding("a", s))
        
        s = """
            try:
                b = 8
            finally:
                try:
                    b = 6
                finally:
                    b = 7"""
        self.failIf(self.find_binding("a", s))
        

if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
