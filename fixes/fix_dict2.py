# Copyright 2007 Google, Inc. All Rights Reserved.

"""Fixer for dict methods, take 2.

This is less correct but  more pragmatic.

.iterkeys   -> .keys
.iteritems  -> .items
.itervalues -> .values
"""

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes import macros

class FixDict2(basefix.BaseFix):

    PATTERN = """
    trailer< '.' method=('iterkeys'|'iteritems'|'itervalues') >
    """

    def transform(self, node):
        results = self.match(node)
        method = results["method"][0].value # Extract method name
        assert method.startswith("iter")
        newmethod = method[4:]
        new = pytree.Node(self.syms.trailer,
                          [pytree.Leaf(token.DOT, '.'),
                           macros.Name(newmethod)])
        new.set_prefix(node.get_prefix())
        new.children[1].set_prefix(node.children[1].get_prefix())
        return new
