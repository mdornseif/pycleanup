# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for exec."""

# Python imports
import token

# Local imports
import pytree
from fixes import basefix


class FixExec(basefix.BaseFix):

    PATTERN = """
    exec_stmt< 'exec' a=any 'in' b=any [',' c=any] >
    |
    exec_stmt< 'exec' (not atom<'(' [any] ')'>) a=any >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        a = results["a"]
        b = results.get("b")
        c = results.get("c")
        args = [a.clone()]
        args[0].set_prefix("")
        if b is not None:
            args.extend([pytree.Leaf(token.COMMA, ","), b.clone()])
        if c is not None:
            args.extend([pytree.Leaf(token.COMMA, ","), c.clone()])
        new = pytree.Node(syms.factor,
                          [pytree.Leaf(token.NAME, "exec"),
                           pytree.Node(syms.trailer,
                                       [pytree.Leaf(token.LPAR, "("),
                                        pytree.Node(syms.arglist, args),
                                        pytree.Leaf(token.RPAR, ")")])])
        new.set_prefix(node.get_prefix())
        return new
