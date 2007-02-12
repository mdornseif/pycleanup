# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that transforms `xyzzy` into repr(xyzzy)."""

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.macros import Call, Name


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
      new = Call(Name("repr"), [expr])
      new.set_prefix(node.get_prefix())
      return new
