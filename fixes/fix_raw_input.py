"""Fixer that changes raw_input(...) into input(...)."""
# Author: Andre Roberge

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.util import Name

class FixRawInput(basefix.BaseFix):

    PATTERN = """
    power<
        'raw_input'
        args=trailer< '(' [any] ')' >
    >
    """

    def transform(self, node):
        results = self.match(node)
        args = results["args"]
        new = pytree.Node(self.syms.power,
                          [Name("input"), args.clone()])
        new.set_prefix(node.get_prefix())
        return new
