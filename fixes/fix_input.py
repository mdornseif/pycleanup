"""Fixer that changes input(...) into eval(input(...))."""
# Author: Andre Roberge

# Local imports
import pytree
import patcomp
from pgen2 import token
from fixes import basefix
from fixes import macros

class FixInput(basefix.BaseFix):

    PATTERN = """
    power<
        'input'
        args=trailer< '(' [any] ')' >
    >
    """

    def transform(self, node):
        new = node.clone()
        new.set_prefix("")
        new = macros.Call(macros.Name("eval"), [new])
        new.set_prefix(node.get_prefix())
        return new
