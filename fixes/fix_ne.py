# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that turns <> into !=.

This is so simple that we don't need the pattern compiler.
"""

# Python imports
import token

# Local imports
import pytree
import pygram

syms = pygram.python_symbols


class FixNe(object):

    def __init__(self, options):
        self.options = options

    def match(self, node):
        return node.type == token.NOTEQUAL and node.value == "<>"

    def transform(self, node):
      new = pytree.Leaf(token.NOTEQUAL, "!=")
      new.set_prefix(node.get_prefix())
      return new
