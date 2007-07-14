"""Fixer that changes input(...) into eval(input(...))."""
# Author: Andre Roberge

# Local imports
from fixes import basefix
from fixes.util import Call, Name

class FixInput(basefix.BaseFix):

    PATTERN = """
    power<
        'input'
        args=trailer< '(' [any] ')' >
    >
    """

    def transform(self, node, results):
        new = node.clone()
        new.set_prefix("")
        new = Call(Name("eval"), [new])
        new.set_prefix(node.get_prefix())
        return new
