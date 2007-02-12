# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for exec."""

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.macros import Comma, Name, Call


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
            args.extend([Comma(), b.clone()])
        if c is not None:
            args.extend([Comma(), c.clone()])

        new = Call(Name("exec"), args)
        new.set_prefix(node.get_prefix())
        return new
