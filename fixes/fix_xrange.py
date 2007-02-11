# Copyright 2007 Google, Inc. All Rights Reserved.

"""Fixer that changes xrange(...) into range(...)."""

# Python imports
import token

# Local imports
import pytree
from fixes import basefix
from fixes import macros

class FixXrange(basefix.BaseFix):

    PATTERN = """
    power<
        'xrange'
        args=trailer< '(' [any] ')' >
    >
    """

    def transform(self, node):
        results = self.match(node)
        args = results["args"]
        new = pytree.Node(self.syms.power,
                          [macros.Name("range"), args.clone()])
        new.set_prefix(node.get_prefix())
        return new
