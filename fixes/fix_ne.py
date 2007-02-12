# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that turns <> into !=.

This is so simple that we don't need the pattern compiler.
"""

# Local imports
import pytree
from pgen2 import token
from fixes import basefix


class FixNe(basefix.BaseFix):

    def compile_pattern(self):
        # Override
        pass

    def match(self, node):
        # Override
        return node.type == token.NOTEQUAL and node.value == "<>"

    def transform(self, node):
      new = pytree.Leaf(token.NOTEQUAL, "!=")
      new.set_prefix(node.get_prefix())
      return new
