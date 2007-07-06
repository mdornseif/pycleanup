"""Fixer/warner for sys.exc_{value,type,traceback}"""
# Author: Collin Winter

# Local imports
from pytree import Leaf
from fixes import basefix


class FixSysexcattrs(basefix.BaseFix):

    PATTERN = """
    power< 'sys'
           trailer< '.' ('exc_value' | 'exc_traceback' | 'exc_type')>
           any* >
    """

    def transform(self, node):
        self.cannot_convert(node, "This attribute is going away in Python 3")
