# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that transforms `xyzzy` into repr(xyzzy)."""

# Python imports
import token

# Local imports
import pytree
from fixes import basefix


class FixRepr(basefix.BaseFix):

    PATTERN = """
    atom < '`' expr=any '`' >
    """

    def transform(self, node):
      results = self.match(node)
      assert results
      expr = results["expr"].clone()
      if expr.type == self.syms.testlist1:
        expr = self.parenthesize(expr)
      new = pytree.Node(self.syms.power,
                        (pytree.Leaf(token.NAME, "repr"),
                         pytree.Node(self.syms.trailer,
                                     (pytree.Leaf(token.LPAR, "("),
                                      expr,
                                      pytree.Leaf(token.RPAR, ")")))))
      new.set_prefix(node.get_prefix())
      return new
