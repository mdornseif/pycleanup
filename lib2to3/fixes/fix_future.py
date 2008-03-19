"""Remove __future__ imports

from __future__ import foo is replaced with an empty line.
"""
# Author: Christian Heimes

# Local imports
from . import basefix
from .util import BlankLine

class FixFuture(basefix.BaseFix):
    PATTERN = """import_from< 'from' module_name="__future__" 'import' any >"""

    # While the order that the tree is traversed does not matter,
    # the postorder traversal fixers are run after the preorder fixers.
    # Forcing this fixer to run in postorder ensures that fixers which check
    # for __future__ can run first.
    order='post'

    def transform(self, node, results):
        return BlankLine()
