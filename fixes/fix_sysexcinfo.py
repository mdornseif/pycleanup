"""Fixer/warner for sys.exc_{info,value,type,traceback}"""
# Author: Collin Winter

# Local imports
from pytree import Leaf
from fixes import basefix


class FixSysexcinfo(basefix.BaseFix):

    PATTERN = """
    power< 'sys' trailer< '.' attr='exc_info'> any* >
    |
    power< 'sys'
           trailer< '.' attr=('exc_value' | 'exc_traceback' | 'exc_type')>
           any* >
    """

    def transform(self, node):
        results = self.match(node)
        assert results
        attr = results['attr']

        if isinstance(attr, Leaf) and attr.value == 'exc_info':
            self.cannot_convert(node,
                                "This function is going away in Python 3")
        else:
            self.cannot_convert(node,
                                "This attribute is going away in Python 3")
