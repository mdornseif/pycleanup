"""Fixer for 'raise E, a1, a2, ...'"""

# Python imports
import token

# Local imports
import pytree
from fixes import basefix

could_not_convert = "At line %d: could not convert: %s"
reason = "At line %d: Python 3's raise will not support providing a traceback"

def get_lineno(node):
    while not isinstance(node, pytree.Leaf):
        if not node.children:
            return
        node = node.children[0]
    return node.lineno

class FixRaise(basefix.BaseFix):

    PATTERN = """
    raise_stmt< 'raise' exc=any ',' a1=any [',' a2=any] >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        
        exc = results["exc"].clone()
        args = [results["a1"].clone()]
        args[0].set_prefix("")
        
        arg2 = results.get("a2")
        if arg2 is not None:
            lineno = get_lineno(node)
            for_output = node.clone()
            for_output.set_prefix("")
            self.logger.warning(could_not_convert % (lineno, for_output))
            self.logger.warning(reason % lineno)
            return node
        
        new = pytree.Node(syms.raise_stmt,
                          [pytree.Leaf(token.NAME, "raise"),
                           exc,
                           pytree.Node(syms.trailer,
                                       [pytree.Leaf(token.LPAR, "("),
                                        pytree.Node(syms.arglist, args),
                                        pytree.Leaf(token.RPAR, ")")])])
        new.set_prefix(node.get_prefix())
        return new
