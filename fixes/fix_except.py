"""Fixer for except statements with named exceptions."""

# Python imports
import token

# Local imports
import pytree
from fixes import basefix

def get_lineno(node):
    while not isinstance(node, pytree.Leaf):
        if not node.children:
            return
        node = node.children[0]
    return node.lineno

class FixExcept(basefix.BaseFix):

    PATTERN = """
    except_clause< 'except' a=any ',' b=any >
    """
    
    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        
        a = results["a"].clone()
        b = results["b"].clone()
        
        if b.type != token.NAME:
            lineno = get_lineno(node)
            self.logger.warning("At line %s, unable to transform: %s" %
                                                                (lineno, node))
            return node
        
        as_leaf = pytree.Leaf(token.NAME, "as")
        as_leaf.set_prefix(' ')
        
        new = pytree.Node(syms.except_clause,
                          [pytree.Leaf(token.NAME, "except"),
                           pytree.Node(syms.test, [a]),
                           as_leaf,
                           pytree.Node(syms.test, [b])])
        new.set_prefix(node.get_prefix())
        return new
