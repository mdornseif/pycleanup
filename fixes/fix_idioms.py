"""Adjust some old Python 2 idioms to their modern counterparts.

* Change some type comparisons to isinstance() calls:
    type(x) == T -> isinstance(x, T)
    type(x) is T -> isinstance(x, T)
    type(x) != T -> not isinstance(x, T)
    type(x) is not T -> not isinstance(x, T)
"""
# Author: Jacques Frechet, Collin Winter

# Local imports
from fixes import basefix
from fixes.util import Call, Comma, Name, Node, syms

CMP = "(n='!=' | '==' | 'is' | n=comp_op< 'is' 'not' >)"

class FixIdioms(basefix.BaseFix):

    PATTERN = """
        comparison< power< 'type' trailer< '(' x=any ')' > > %s T=any > |
        comparison< T=any %s power< 'type' trailer< '(' x=any ')' > > >
    """ % (CMP, CMP)

    def transform(self, node, results):
        x = results['x'].clone() # The thing inside of type()
        T = results['T'].clone() # The type being compared against
        x.set_prefix('')
        T.set_prefix(' ')
        test = Call(Name('isinstance'), [x, Comma(), T])
        if "n" in results:
            test.set_prefix(" ")
            test = Node(syms.not_test, [Name('not'), test])
        test.set_prefix(node.get_prefix())
        return test
