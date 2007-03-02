#!/usr/bin/env python2.5
""" Test suite for Grammar.txt. This is the place to add tests for
changes to 2to3's grammar, such as those merging the grammars for
Python 2 and 3. """
# Author: Collin Winter

# Testing imports
import support
if __name__ == '__main__':
    support.adjust_path()

# Python imports
import os.path

# Local imports
import pytree
from pgen2 import driver
from pgen2.parse import ParseError


grammar_path = os.path.join(os.path.dirname(__file__), "..", "Grammar.txt")
grammar = driver.load_grammar(grammar_path)
driver = driver.Driver(grammar, convert=pytree.convert)

class GrammarTest(support.TestCase):
    def validate(self, code):
        driver.parse_string(support.reformat(code), debug=True)
        
    def invalid_syntax(self, code):
        try:
            self.validate(code)
        except ParseError:
            pass


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


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)
