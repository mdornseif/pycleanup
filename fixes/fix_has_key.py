# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for has_key()."""

# Python imports
import token

# Local imports
import pytree
from fixes import basefix
from fixes.macros import Name


class FixHasKey(basefix.BaseFix):

    PATTERN = """
    anchor=power<
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
    |
    negation=not_test<
        'not'
        anchor=power<
            before=any+
            trailer< '.' 'has_key' >
            trailer<
                '('
                ( not(arglist | argument<any '=' any>) arg=any
                | arglist<(not argument<any '=' any>) arg=any ','>
                )
                ')'
            >
        >
    >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        if (node.parent.type == syms.not_test and
            self.pattern.match(node.parent)):
            # Don't transform a node matching the first alternative of the
            # pattern when its parent matches the second alternative
            return None
        negation = results.get("negation")
        anchor = results["anchor"]
        prefix = node.get_prefix()
        before = [n.clone() for n in results["before"]]
        arg = results["arg"].clone()
        after = results.get("after")
        if after:
            after = [n.clone() for n in after]
        if arg.type in (syms.comparison, syms.not_test, syms.and_test,
                        syms.or_test, syms.test, syms.lambdef, syms.argument):
            arg = self.parenthesize(arg)
        if len(before) == 1:
            before = before[0]
        else:
            before = pytree.Node(syms.power, before)
        before.set_prefix(" ")
        n_op = Name("in")
        n_op.set_prefix(" ")
        if negation:
            n_not = Name("not")
            n_not.set_prefix(" ")
            n_op = pytree.Node(syms.comp_op, (n_not, n_op))
        new = pytree.Node(syms.comparison, (arg, n_op, before))
        if after:
            new = self.parenthesize(new)
            new = pytree.Node(syms.power, (new,) + tuple(after))
        if node.parent.type in (syms.comparison, syms.expr, syms.xor_expr,
                                syms.and_expr, syms.shift_expr,
                                syms.arith_expr, syms.term,
                                syms.factor, syms.power):
            new = self.parenthesize(new)
        new.set_prefix(prefix)
        return new
