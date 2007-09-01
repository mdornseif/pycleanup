"""Adjust some old Python 2 idioms to their modern counterparts.

* Change some type comparisons to isinstance() calls:
    type(x) == T -> isinstance(x, T)
    type(x) is T -> isinstance(x, T)
    type(x) != T -> not isinstance(x, T)
    type(x) is not T -> not isinstance(x, T)
    
* Change "while 1:" into "while True:".
"""
# Author: Jacques Frechet, Collin Winter

# Local imports
from fixes import basefix
from fixes.util import Call, Comma, Name, Node, syms

CMP = "(n='!=' | '==' | 'is' | n=comp_op< 'is' 'not' >)"
TYPE = "power< 'type' trailer< '(' x=any ')' > >"

class FixIdioms(basefix.BaseFix):

    explicit = True # The user must ask for this fixer

    PATTERN = """
        isinstance=comparison< %s %s T=any > |
        isinstance=comparison< T=any %s %s > |
        while_stmt< 'while' while='1' ':' any+ >
    """ % (TYPE, CMP, CMP, TYPE)

    def transform(self, node, results):
        if "isinstance" in results:
            return self.transform_isinstance(node, results)
        elif "while" in results:
            return self.transform_while(node, results)
        else:
            raise RuntimeError("Invalid match")

    def transform_isinstance(self, node, results):
        x = results["x"].clone() # The thing inside of type()
        T = results["T"].clone() # The type being compared against
        x.set_prefix("")
        T.set_prefix(" ")
        test = Call(Name("isinstance"), [x, Comma(), T])
        if "n" in results:
            test.set_prefix(" ")
            test = Node(syms.not_test, [Name("not"), test])
        test.set_prefix(node.get_prefix())
        return test

    def transform_while(self, node, results):
        one = results["while"]
        one.replace(Name("True", prefix=one.get_prefix()))
