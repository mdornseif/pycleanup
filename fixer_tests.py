""" Test suite for the fixer modules """
# Author: Collin Winter

# Python imports
from StringIO import StringIO
import unittest
import logging

# Local imports
import pytree
import refactor


# We wrap the RefactoringTool's fixer objects so we can intercept
#  the call to set_filename() and so modify the fixers' logging objects.
# This allows us to make sure that certain code chunks produce certain
#  warnings.
class Fixer(object):
    def __init__(self, fixer, handler):
        self.fixer = fixer
        self.handler = handler

    def __getattr__(self, attr):
        return getattr(self.fixer, attr)

    def set_filename(self, filename):
        self.fixer.set_filename(filename)
        self.fixer.logger.addHandler(self.handler)

class Options:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.verbose = False

class FixerTestCase(unittest.TestCase):
    def setUp(self):
        options = Options(fix=[self.fixer])
        self.refactor = refactor.RefactoringTool(options)

        self.logging_stream = StringIO()
        sh = logging.StreamHandler(self.logging_stream)
        sh.setFormatter(logging.Formatter("%(message)s"))
        self.refactor.fixers = [Fixer(f, sh) for f in self.refactor.fixers]

    def check(self, before, after):
        before += "\n"
        after += "\n"
        refactored = self.refactor_stream("<string>", StringIO(before))
        self.failUnlessEqual(after, refactored)

    def warns(self, before, after, message):
        self.check(before, after)

        self.failUnless(message in self.logging_stream.getvalue())

    def refactor_stream(self, stream_name, stream):
        try:
            tree = self.refactor.driver.parse_stream(stream)
        except Exception, err:
            raise
            self.log_error("Can't parse %s: %s: %s",
                           filename, err.__class__.__name__, err)
            return
        self.refactor.refactor_tree(tree, stream_name)
        return str(tree)


class Test_ne(FixerTestCase):
    fixer = "ne"

    def test_1(self):
        b = """if x <> y:
            pass"""

        a = """if x != y:
            pass"""
        self.check(b, a)

    def test_2(self):
        b = """if x<>y:
            pass"""

        a = """if x!=y:
            pass"""
        self.check(b, a)

    def test_3(self):
        b = """if x<>y<>z:
            pass"""

        a = """if x!=y!=z:
            pass"""
        self.check(b, a)

class Test_has_key(FixerTestCase):
    fixer = "has_key"

    def test_1(self):
        b = """x = d.has_key("x") or d.has_key("y")"""
        a = """x = "x" in d or "y" in d"""
        self.check(b, a)

    def test_2(self):
        b = """x = a.b.c.d.has_key("x") ** 3"""
        a = """x = ("x" in a.b.c.d) ** 3"""
        self.check(b, a)

    def test_3(self):
        b = """x = a.b.has_key(1 + 2).__repr__()"""
        a = """x = (1 + 2 in a.b).__repr__()"""
        self.check(b, a)

    def test_4(self):
        b = """x = a.b.has_key(1 + 2).__repr__() ** -3 ** 4"""
        a = """x = (1 + 2 in a.b).__repr__() ** -3 ** 4"""
        self.check(b, a)

    def test_5(self):
        b = """x = a.has_key(f or g)"""
        a = """x = (f or g) in a"""
        self.check(b, a)

    def test_6(self):
        b = """x = a + b.has_key(c)"""
        a = """x = a + (c in b)"""
        self.check(b, a)

    def test_7(self):
        b = """x = a.has_key(lambda: 12)"""
        a = """x = (lambda: 12) in a"""
        self.check(b, a)

    def test_8(self):
        b = """x = a.has_key(a for a in b)"""
        a = """x = (a for a in b) in a"""
        self.check(b, a)

    def test_9(self):
        b = """if not a.has_key(b): pass"""
        a = """if b not in a: pass"""
        self.check(b, a)

    def test_10(self):
        b = """if not a.has_key(b).__repr__(): pass"""
        a = """if not (b in a).__repr__(): pass"""
        self.check(b, a)

    def test_11(self):
        b = """if not a.has_key(b) ** 2: pass"""
        a = """if not (b in a) ** 2: pass"""
        self.check(b, a)

class Test_apply(FixerTestCase):
    fixer = "apply"

    def test_1(self):
        b = """x = apply(f, g + h)"""
        a = """x = f(*g + h)"""
        self.check(b, a)

    def test_2(self):
        b = """y = apply(f, g, h)"""
        a = """y = f(*g, **h)"""
        self.check(b, a)

    def test_3(self):
        b = """z = apply(fs[0], g or h, h or g)"""
        a = """z = fs[0](*g or h, **h or g)"""
        self.check(b, a)

    def test_4(self):
        b = """apply(f, (x, y) + t)"""
        a = """f(*(x, y) + t)"""
        self.check(b, a)

    def test_5(self):
        b = """apply(f, args,)"""
        a = """f(*args)"""
        self.check(b, a)

    def test_6(self):
        b = """apply(f, args, kwds,)"""
        a = """f(*args, **kwds)"""
        self.check(b, a)

    # Test that complex functions are parenthesized

    def test_7(self):
        b = """x = apply(f+g, args)"""
        a = """x = (f+g)(*args)"""
        self.check(b, a)

    def test_8(self):
        b = """x = apply(f*g, args)"""
        a = """x = (f*g)(*args)"""
        self.check(b, a)

    def test_9(self):
        b = """x = apply(f**g, args)"""
        a = """x = (f**g)(*args)"""
        self.check(b, a)

    # But dotted names etc. not

    def test_10(self):
        b = """x = apply(f.g, args)"""
        a = """x = f.g(*args)"""
        self.check(b, a)

    def test_11(self):
        b = """x = apply(f[x], args)"""
        a = """x = f[x](*args)"""
        self.check(b, a)

    def test_12(self):
        b = """x = apply(f(), args)"""
        a = """x = f()(*args)"""
        self.check(b, a)

    # Extreme case
    def test_13(self):
        b = """x = apply(a.b.c.d.e.f, args, kwds)"""
        a = """x = a.b.c.d.e.f(*args, **kwds)"""
        self.check(b, a)

    # XXX Comments in weird places still get lost
    def test_14(self):
        b = """apply(   # foo
          f, # bar
          args)"""
        a = """f(*args)"""
        self.check(b, a)

    # These should *not* be touched

    def test_15(self):
        b = """apply()"""
        a = """apply()"""
        self.check(b, a)

    def test_16(self):
        b = """apply(f)"""
        a = """apply(f)"""
        self.check(b, a)

    def test_17(self):
        b = """apply(f,)"""
        a = """apply(f,)"""
        self.check(b, a)

    def test_18(self):
        b = """apply(f, args, kwds, extras)"""
        a = """apply(f, args, kwds, extras)"""
        self.check(b, a)

    def test_19(self):
        b = """apply(f, *args, **kwds)"""
        a = """apply(f, *args, **kwds)"""
        self.check(b, a)

    def test_20(self):
        b = """apply(f, *args)"""
        a = """apply(f, *args)"""
        self.check(b, a)

    def test_21(self):
        b = """apply(func=f, args=args, kwds=kwds)"""
        a = """apply(func=f, args=args, kwds=kwds)"""
        self.check(b, a)

    def test_22(self):
        b = """apply(f, args=args, kwds=kwds)"""
        a = """apply(f, args=args, kwds=kwds)"""
        self.check(b, a)

    def test_23(self):
        b = """apply(f, args, kwds=kwds)"""
        a = """apply(f, args, kwds=kwds)"""
        self.check(b, a)


class Test_intern(FixerTestCase):
    fixer = "intern"

    def test_1(self):
        b = """x = intern(a)"""
        a = """x = sys.intern(a)"""
        self.check(b, a)

    def test_2(self):
        b = """y = intern("b" # test
              )"""
        a = """y = sys.intern("b" # test
              )"""
        self.check(b, a)

    def test_3(self):
        b = """z = intern(a+b+c.d,)"""
        a = """z = sys.intern(a+b+c.d,)"""
        self.check(b, a)

    def test_4(self):
        b = """intern("y%s" % 5).replace("y", "")"""
        a = """sys.intern("y%s" % 5).replace("y", "")"""
        self.check(b, a)

    # These should not be refactored

    def test_5(self):
        b = """intern(a=1)"""
        a = """intern(a=1)"""
        self.check(b, a)

    def test_6(self):
        b = """intern(f, g)"""
        a = """intern(f, g)"""
        self.check(b, a)

    def test_7(self):
        b = """intern(*h)"""
        a = """intern(*h)"""
        self.check(b, a)

    def test_8(self):
        b = """intern(**i)"""
        a = """intern(**i)"""
        self.check(b, a)

class Test_print(FixerTestCase):
    fixer = "print"

    def test_1(self):
        b = """print 1, 1+1, 1+1+1"""
        a = """Print(1, 1+1, 1+1+1)"""
        self.check(b, a)

    def test_2(self):
        b = """print 1, 2"""
        a = """Print(1, 2)"""
        self.check(b, a)

    def test_3(self):
        b = """print"""
        a = """Print()"""
        self.check(b, a)

    # trailing commas

    def test_4(self):
        b = """print 1, 2, 3,"""
        a = """Print(1, 2, 3, end=' ')"""
        self.check(b, a)

    def test_5(self):
        b = """print 1, 2,"""
        a = """Print(1, 2, end=' ')"""
        self.check(b, a)

    def test_6(self):
        b = """print 1,"""
        a = """Print(1, end=' ')"""
        self.check(b, a)

    # >> stuff

    # no trailing comma
    def test_7(self):
        b = """print >>sys.stderr, 1, 2, 3"""
        a = """Print(1, 2, 3, file=sys.stderr)"""
        self.check(b, a)

    # trailing comma
    def test_8(self):
        b = """print >>sys.stderr, 1, 2,"""
        a = """Print(1, 2, end=' ', file=sys.stderr)"""
        self.check(b, a)

    # no trailing comma
    def test_9(self):
        b = """print >>sys.stderr, 1+1"""
        a = """Print(1+1, file=sys.stderr)"""
        self.check(b, a)

    # spaces before sys.stderr
    def test_10(self):
        b = """print >>  sys.stderr"""
        a = """Print(file=sys.stderr)"""
        self.check(b, a)


class Test_exec(FixerTestCase):
    fixer = "exec"

    def test_1(self):
        b = """exec code"""
        a = """exec(code)"""
        self.check(b, a)

    def test_2(self):
        b = """exec code in ns"""
        a = """exec(code, ns)"""
        self.check(b, a)

    def test_3(self):
        b = """exec code in ns1, ns2"""
        a = """exec(code, ns1, ns2)"""
        self.check(b, a)

    def test_4(self):
        b = """exec (a.b()) in ns"""
        a = """exec((a.b()), ns)"""
        self.check(b, a)

    def test_5(self):
        b = """exec a.b() + c in ns"""
        a = """exec(a.b() + c, ns)"""
        self.check(b, a)

    # These should not be touched

    def test_6(self):
        b = """exec(code)"""
        a = """exec(code)"""
        self.check(b, a)

    def test_7(self):
        b = """exec (code)"""
        a = """exec (code)"""
        self.check(b, a)

    def test_8(self):
        b = """exec(code, ns)"""
        a = """exec(code, ns)"""
        self.check(b, a)

    def test_9(self):
        b = """exec(code, ns1, ns2)"""
        a = """exec(code, ns1, ns2)"""
        self.check(b, a)


class Test_repr(FixerTestCase):
    fixer = "repr"

    def test_1(self):
        b = """x = `1 + 2`"""
        a = """x = repr(1 + 2)"""
        self.check(b, a)

    def test_2(self):
        b = """y = `x`"""
        a = """y = repr(x)"""
        self.check(b, a)

    def test_3(self):
        b = """z = `y`.__repr__()"""
        a = """z = repr(y).__repr__()"""
        self.check(b, a)

    def test_4(self):
        b = """x = `1, 2, 3`"""
        a = """x = repr((1, 2, 3))"""
        self.check(b, a)

    def test_5(self):
        b = """x = `1 + `2``"""
        a = """x = repr(1 + repr(2))"""
        self.check(b, a)

    def test_6(self):
        b = """x = `1, 2 + `3, 4``"""
        a = """x = repr((1, 2 + repr((3, 4))))"""
        self.check(b, a)

class Test_except():
    fixer = "except"

    def test_1(self):
        b = """
            try:
                pass
            except Exception, (f, e):
                pass
            except ImportError, e:
                pass"""

        a = """
            try:
                pass
            except Exception as (f, e):
                pass
            except ImportError as e:
                pass"""
        self.check(b, a)

    def test_2(self):
        b = """
            try:
                pass
            except (RuntimeError, ImportError), e:
                pass"""

        a = """
            try:
                pass
            except (RuntimeError, ImportError) as e:
                pass"""
        self.check(b, a)

    def test_3(self):
        b = """
            try:
                pass
            except Exception, (a, b):
                pass"""

        a = """
            try:
                pass
            except Exception as (a, b):
                pass"""
        self.check(b, a)

    def test_4(self):
        b = """
            try:
                pass
            except Exception, d[5]:
                pass"""

        a = """
            try:
                pass
            except Exception as xxx_todo_changeme:
                d[5] = xxx_todo_changeme
                pass"""
        self.check(b, a)

    def test_5(self):
        b = """
            try:
                pass
            except Exception, a.foo:
                pass"""

        a = """
            try:
                pass
            except Exception as xxx_todo_changeme1:
                a.foo = xxx_todo_changeme1
                pass"""
        self.check(b, a)

    def test_6(self):
        b = """
            try:
                pass
            except Exception, a().foo:
                pass"""

        a = """
            try:
                pass
            except Exception as xxx_todo_changeme2:
                a().foo = xxx_todo_changeme2
                pass"""
        self.check(b, a)

    # These should not be touched:

    def test_7(self):
        b = """
            try:
                pass
            except:
                pass"""

        a = """
            try:
                pass
            except:
                pass"""
        self.check(b, a)

    def test_8(self):
        b = """
            try:
                pass
            except Exception:
                pass"""

        a = """
            try:
                pass
            except Exception:
                pass"""
        self.check(b, a)

    def test_9(self):
        b = """
            try:
                pass
            except (Exception, SystemExit):
                pass"""

        a = """
            try:
                pass
            except (Exception, SystemExit):
                pass"""
        self.check(b, a)


class Test_raise(FixerTestCase):
    fixer = "raise"

    def test_1(self):
        b = """raise Exception, 5"""
        a = """raise Exception(5)"""
        self.check(b, a)

    def test_2(self):
        b = """raise Exception,5"""
        a = """raise Exception(5)"""
        self.check(b, a)

    def test_3(self):
        b = """raise Exception, (5, 6, 7)"""
        a = """raise Exception((5, 6, 7))"""
        self.check(b, a)

    # These should not be touched

    def test_4(self):
        b = """raise Exception"""
        a = """raise Exception"""
        self.check(b, a)

    def test_5(self):
        b = """raise Exception(5, 6)"""
        a = """raise Exception(5, 6)"""
        self.check(b, a)

    # These should result in traceback-assignment

    def test_tb_1(self):
        b = """def foo():
                    raise Exception, 5, 6"""
        a = """def foo():
                    xxx_todo_changeme = Exception(5)
                    xxx_todo_changeme.__traceback__ = 6
                    raise xxx_todo_changeme"""
        self.check(b, a)

    def test_tb_2(self):
        b = """def foo():
                    a = 5
                    raise Exception, 5, 6
                    b = 6"""
        a = """def foo():
                    a = 5
                    xxx_todo_changeme1 = Exception(5)
                    xxx_todo_changeme1.__traceback__ = 6
                    raise xxx_todo_changeme1
                    b = 6"""
        self.check(b, a)

    def test_tb_3(self):
        b = """def foo():
                    raise Exception,5,6"""
        a = """def foo():
                    xxx_todo_changeme2 = Exception(5)
                    xxx_todo_changeme2.__traceback__ = 6
                    raise xxx_todo_changeme2"""
        self.check(b, a)

    def test_tb_4(self):
        b = """def foo():
                    a = 5
                    raise Exception,5,6
                    b = 6"""
        a = """def foo():
                    a = 5
                    xxx_todo_changeme3 = Exception(5)
                    xxx_todo_changeme3.__traceback__ = 6
                    raise xxx_todo_changeme3
                    b = 6"""
        self.check(b, a)

    def test_tb_5(self):
        b = """def foo():
                    raise Exception, (5, 6, 7), 6"""
        a = """def foo():
                    xxx_todo_changeme4 = Exception((5, 6, 7))
                    xxx_todo_changeme4.__traceback__ = 6
                    raise xxx_todo_changeme4"""
        self.check(b, a)

    def test_tb_6(self):
        b = """def foo():
                    a = 5
                    raise Exception, (5, 6, 7), 6
                    b = 6"""
        a = """def foo():
                    a = 5
                    xxx_todo_changeme5 = Exception((5, 6, 7))
                    xxx_todo_changeme5.__traceback__ = 6
                    raise xxx_todo_changeme5
                    b = 6"""
        self.check(b, a)


class Test_throw(FixerTestCase):
    fixer = "throw"

    def test_1(self):
        b = """g.throw(Exception, 5)"""
        a = """g.throw(Exception(5))"""
        self.check(b, a)

    def test_2(self):
        b = """g.throw(Exception,5)"""
        a = """g.throw(Exception(5))"""
        self.check(b, a)

    def test_3(self):
        b = """g.throw(Exception, (5, 6, 7))"""
        a = """g.throw(Exception((5, 6, 7)))"""
        self.check(b, a)

    def test_4(self):
        b = """5 + g.throw(Exception, 5)"""
        a = """5 + g.throw(Exception(5))"""
        self.check(b, a)

    # These should not be touched

    def test_5(self):
        b = """g.throw(Exception)"""
        a = """g.throw(Exception)"""
        self.check(b, a)

    def test_6(self):
        b = """g.throw(Exception(5, 6))"""
        a = """g.throw(Exception(5, 6))"""
        self.check(b, a)

    def test_7(self):
        b = """5 + g.throw(Exception(5, 6))"""
        a = """5 + g.throw(Exception(5, 6))"""
        self.check(b, a)

    # These should result in traceback-assignment

    def test_tb_1(self):
        b = """def foo():
                    g.throw(Exception, 5, 6)"""
        a = """def foo():
                    xxx_todo_changeme6 = Exception(5)
                    xxx_todo_changeme6.__traceback__ = 6
                    g.throw(xxx_todo_changeme6)"""
        self.check(b, a)

    def test_tb_2(self):
        b = """def foo():
                    a = 5
                    g.throw(Exception, 5, 6)
                    b = 6"""
        a = """def foo():
                    a = 5
                    xxx_todo_changeme7 = Exception(5)
                    xxx_todo_changeme7.__traceback__ = 6
                    g.throw(xxx_todo_changeme7)
                    b = 6"""
        self.check(b, a)

    def test_tb_3(self):
        b = """def foo():
                    g.throw(Exception,5,6)"""
        a = """def foo():
                    xxx_todo_changeme8 = Exception(5)
                    xxx_todo_changeme8.__traceback__ = 6
                    g.throw(xxx_todo_changeme8)"""
        self.check(b, a)

    def test_tb_4(self):
        b = """def foo():
                    a = 5
                    g.throw(Exception,5,6)
                    b = 6"""
        a = """def foo():
                    a = 5
                    xxx_todo_changeme9 = Exception(5)
                    xxx_todo_changeme9.__traceback__ = 6
                    g.throw(xxx_todo_changeme9)
                    b = 6"""
        self.check(b, a)

    def test_tb_5(self):
        b = """def foo():
                    g.throw(Exception, (5, 6, 7), 6)"""
        a = """def foo():
                    xxx_todo_changeme10 = Exception((5, 6, 7))
                    xxx_todo_changeme10.__traceback__ = 6
                    g.throw(xxx_todo_changeme10)"""
        self.check(b, a)

    def test_tb_6(self):
        b = """def foo():
                    a = 5
                    g.throw(Exception, (5, 6, 7), 6)
                    b = 6"""
        a = """def foo():
                    a = 5
                    xxx_todo_changeme11 = Exception((5, 6, 7))
                    xxx_todo_changeme11.__traceback__ = 6
                    g.throw(xxx_todo_changeme11)
                    b = 6"""
        self.check(b, a)

    def test_tb_7(self):
        b = """def foo():
                    a + g.throw(Exception, 5, 6)"""
        a = """def foo():
                    xxx_todo_changeme12 = Exception(5)
                    xxx_todo_changeme12.__traceback__ = 6
                    a + g.throw(xxx_todo_changeme12)"""
        self.check(b, a)

    def test_tb_8(self):
        b = """def foo():
                    a = 5
                    a + g.throw(Exception, 5, 6)
                    b = 6"""
        a = """def foo():
                    a = 5
                    xxx_todo_changeme13 = Exception(5)
                    xxx_todo_changeme13.__traceback__ = 6
                    a + g.throw(xxx_todo_changeme13)
                    b = 6"""
        self.check(b, a)


class Test_long(FixerTestCase):
    fixer = "long"

    def test_1(self):
        b = """x = long(x)"""
        a = """x = int(x)"""
        self.check(b, a)

    def test_2(self):
        b = """y = isinstance(x, long)"""
        a = """y = isinstance(x, int)"""
        self.check(b, a)

    def test_3(self):
        b = """z = type(x) in (int, long)"""
        a = """z = type(x) in (int, int)"""
        self.check(b, a)

    def test_4(self):
        b = """a = 12L"""
        a = """a = 12"""
        self.check(b, a)

    def test_5(self):
        b = """b = 0x12l"""
        a = """b = 0x12"""
        self.check(b, a)

    # These should not be touched

    def test_6(self):
        b = """a = 12"""
        a = """a = 12"""
        self.check(b, a)

    def test_7(self):
        b = """b = 0x12"""
        a = """b = 0x12"""
        self.check(b, a)

    def test_8(self):
        b = """c = 3.14"""
        a = """c = 3.14"""
        self.check(b, a)


class Test_sysexcinfo(FixerTestCase):
    fixer = "sysexcinfo"

    def test_1(self):
        s = """sys.exc_info()"""
        self.warns(s, s, "This function is going away")

    def test_2(self):
        s = """if sys.exc_info()[1] == 1:
                    pass"""

        self.warns(s, s, "This function is going away")

    def test_3(self):
        s = """f = sys.exc_info"""
        self.warns(s, s, "This function is going away")

    def test_4(self):
        s = """f = sys.exc_type + ":" + sys.exc_value"""
        self.warns(s, s, "This attribute is going away")

if __name__ == "__main__":
    import sys
    if not sys.argv[1:]:
        sys.argv.append("-v")
    unittest.main()
