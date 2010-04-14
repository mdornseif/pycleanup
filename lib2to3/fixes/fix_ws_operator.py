"""Fixer that changes 'a +b' into 'a + b'.

This also changes '{a :b}' into '{a: b}', but does not touch other
uses of colons.  It does not touch other uses of whitespace.

"""

from .. import pytree
from ..pgen2 import token
from .. import fixer_base

from ..pygram import python_symbols as syms

class FixWsOperator(fixer_base.BaseFix):

    explicit = False

    PATTERN = """
    any<(not('%'|'+'|'-'|'*'|'/'|','|'|(') any)+ ('%'|'+'|'-'|'*'|'/') (not('%'|'+'|'-'|'*'|'/'|',') any)>
    """

    PERCENT = pytree.Leaf(token.PERCENT, u"%")
    PLUS = pytree.Leaf(token.PLUS, u"+")
    MINUS = pytree.Leaf(token.MINUS, u"-")
    STAR = pytree.Leaf(token.STAR, u"*")
    SLASH = pytree.Leaf(token.SLASH, u"/")
    SEPS = (PERCENT, PLUS, MINUS, STAR, SLASH)
    
    def transform(self, node, results):
        new = node.clone()
        seenoperator = False
        for child in new.children:
            if child in self.SEPS:
                prefix = child.prefix
                if not prefix or (prefix.isspace() and u"\n" not in prefix):
                    child.prefix = u" "
                seenoperator = True
            else:
                if seenoperator:
                    prefix = child.prefix
                    if not prefix or (prefix.isspace() and u"\n" not in prefix):
                        child.prefix = u" "
                seenoperator = False
        return new
