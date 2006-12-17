# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for exec."""

# Python imports
import token

# Local imports
import pytree
import patcomp
import pygram

syms = pygram.python_symbols
pat_compile = patcomp.PatternCompiler().compile_pattern

PATTERN = """
exec_stmt< 'exec' a=any 'in' b=any [',' c=any] >
|
exec_stmt< 'exec' (not atom<'(' [any] ')'>) a=any >
"""


class FixExec(object):

    def __init__(self, options):
        self.options = options
        self.pattern = pat_compile(PATTERN)

    def match(self, node):
        results = {}
        return self.pattern.match(node, results) and results

    def transform(self, node):
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
                
