"""Fixer for basestring -> str."""
# Author: Christian Heimes

# Local imports
from fixes import basefix
from fixes.util import Name

class FixBasestring(basefix.BaseFix):

    PATTERN = "'basestring'"

    def transform(self, node, results):
        return Name("str", prefix=node.get_prefix())
