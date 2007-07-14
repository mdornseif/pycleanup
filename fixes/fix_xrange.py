# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that changes xrange(...) into range(...)."""

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.util import Name

class FixXrange(basefix.BaseFix):

    PATTERN = """
    power<
        'xrange'
        args=trailer< '(' [any] ')' >
    >
    """

    def transform(self, node, results):
        args = results["args"]
        new = pytree.Node(self.syms.power,
                          [Name("range"), args.clone()])
        new.set_prefix(node.get_prefix())
        return new
