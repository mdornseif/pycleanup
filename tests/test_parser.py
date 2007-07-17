#!/usr/bin/env python2.5
"""Test suite for 2to3's parser and grammar files.

This is the place to add tests for changes to 2to3's grammar, such as those
merging the grammars for Python 2 and 3. In addition to specific tests for
parts of the grammar we've changed, we also make sure we can parse the
test_grammar.py files from both Python 2 and Python 3.
"""
# Author: Collin Winter

# Testing imports
import support
from support import driver, test_dir

# Python imports
import os
import os.path

# Local imports
from pgen2.parse import ParseError


class GrammarTest(support.TestCase):
    def validate(self, code):
        support.parse_string(code)

    def invalid_syntax(self, code):
        try:
            self.validate(code)
        except ParseError:
            pass
        else:
            raise AssertionError("Syntax shouldn't have been valid")


class TestRaiseChanges(GrammarTest):
    def test_2x_style_1(self):
        self.validate("raise")

    def test_2x_style_2(self):
        self.validate("raise E, V")

    def test_2x_style_3(self):
        self.validate("raise E, V, T")

    def test_2x_style_invalid_1(self):
        self.invalid_syntax("raise E, V, T, Z")

    def test_3x_style(self):
        self.validate("raise E1 from E2")

    def test_3x_style_invalid_1(self):
        self.invalid_syntax("raise E, V from E1")

    def test_3x_style_invalid_2(self):
        self.invalid_syntax("raise E from E1, E2")

    def test_3x_style_invalid_3(self):
        self.invalid_syntax("raise from E1, E2")

    def test_3x_style_invalid_4(self):
        self.invalid_syntax("raise E from")


# Adapated from Python 3's Lib/test/test_grammar.py:GrammarTests.testFuncdef
class TestFunctionAnnotations(GrammarTest):
    def test_1(self):
        self.validate("""def f(x) -> list: pass""")

    def test_2(self):
        self.validate("""def f(x:int): pass""")

    def test_3(self):
        self.validate("""def f(*x:str): pass""")

    def test_4(self):
        self.validate("""def f(**x:float): pass""")

    def test_5(self):
        self.validate("""def f(x, y:1+2): pass""")

    def test_6(self):
        self.validate("""def f(a, (b:1, c:2, d)): pass""")

    def test_7(self):
        self.validate("""def f(a, (b:1, c:2, d), e:3=4, f=5, *g:6): pass""")

    def test_8(self):
        s = """def f(a, (b:1, c:2, d), e:3=4, f=5,
                        *g:6, h:7, i=8, j:9=10, **k:11) -> 12: pass"""
        self.validate(s)


class TestExcept(GrammarTest):
    def test_new(self):
        s = """
            try:
                x
            except E as N:
                y"""
        self.validate(s)

    def test_old(self):
        s = """
            try:
                x
            except E, N:
                y"""
        self.validate(s)


# Adapted from Python 3's Lib/test/test_grammar.py:GrammarTests.testAtoms       
class TestSetLiteral(GrammarTest):
    def test_1(self):
        self.validate("""x = {'one'}""")

    def test_2(self):
        self.validate("""x = {'one', 1,}""")

    def test_3(self):
        self.validate("""x = {'one', 'two', 'three'}""")

    def test_4(self):
        self.validate("""x = {2, 3, 4,}""")


class TestNumericLiterals(GrammarTest):
    def test_new_octal_notation(self):
        self.validate("""0o7777777777777""")
        self.invalid_syntax("""0o7324528887""")

    def test_new_binary_notation(self):
        self.validate("""0b101010""")
        self.invalid_syntax("""0b0101021""")


class TestClassDef(GrammarTest):
    def test_new_syntax(self):
        self.validate("class B(t=7): pass")
        self.validate("class B(t, *args): pass")
        self.validate("class B(t, **kwargs): pass")
        self.validate("class B(t, *args, **kwargs): pass")
        self.validate("class B(t, y=9, *args, **kwargs): pass")


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