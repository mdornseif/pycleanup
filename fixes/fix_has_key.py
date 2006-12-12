# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for has_key()."""

# Python imports
import token

# Local imports
import pytree
import patcomp
import pygram

syms = pygram.python_symbols
pat_compile = patcomp.PatternCompiler().compile_pattern

PATTERN = """
power<
    before=any+
    trailer< '.' 'has_key' >
    trailer<
        '('
        ( not(arglist | argument<any '=' any>) arg=any
        | arglist<(not argument<any '=' any>) arg=any ','>
        )
        ')'
    >
    after=any*
>
"""


class FixHasKey(object):

    def __init__(self, options):
        self.options = options
        self.pattern = pat_compile(PATTERN)

    def match(self, node):
        results = {}
        return self.pattern.match(node, results) and results

    def transform(self, node):
        results = self.match(node)
        assert results
        prefix = node.get_prefix()
        before = [n.clone() for n in results["before"]]
        arg = results["arg"].clone()
        after = results["after"]
        if after:
            after = [n.clone() for n in after]
        if arg.type in (syms.comparison, syms.not_test, syms.and_test,
                        syms.or_test, syms.test, syms.lambdef, syms.argument):
            arg = pygram.parenthesize(arg)
        if len(before) == 1:
            before = before[0]
        else:
            before = pytree.Node(syms.power, before)
        before.set_prefix(" ")
        n_in = pytree.Leaf(token.NAME, "in")
        n_in.set_prefix(" ")
        new = pytree.Node(syms.comparison, (arg, n_in, before))
        if after:
            new = pygram.parenthesize(new)
            new = pytree.Node(syms.power, (new,) + tuple(after))
        if node.parent.type in (syms.comparison, syms.expr, syms.xor_expr,
                                syms.and_expr, syms.shift_expr, syms.arith_expr,
                                syms.term, syms.factor, syms.power):
            new = pygram.parenthesize(new)
        new.set_prefix(prefix)
        return new
