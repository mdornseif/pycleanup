# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for apply()."""

# Python imports
import token

# Local imports
import pytree
from fixes import basefix


class FixApply(basefix.BaseFix):

    PATTERN = """
    power< 'apply'
        trailer<
            '('
            arglist<
                (not argument<NAME '=' any>) func=any ','
                (not argument<NAME '=' any>) args=any [','
                (not argument<NAME '=' any>) kwds=any] [',']
            >
            ')'
        >
    >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        func = results["func"]
        args = results["args"]
        kwds = results.get("kwds")
        prefix = node.get_prefix()
        func = func.clone()
        if (func.type not in (token.NAME, syms.atom) and
            (func.type != syms.power or
             func.children[-2].type == token.DOUBLESTAR)):
            # Need to parenthesize
            func = self.parenthesize(func)
        func.set_prefix("")
        args = args.clone()
        args.set_prefix("")
        if kwds is not None:
            kwds = kwds.clone()
            kwds.set_prefix("")
        l_newargs = [pytree.Leaf(token.STAR, "*"), args]
        if kwds is not None:
            l_newargs.extend([pytree.Leaf(token.COMMA, ","),
                              pytree.Leaf(token.DOUBLESTAR, "**"),
                              kwds])
            l_newargs[-2].set_prefix(" ") # that's the ** token
        # XXX Sometimes we could be cleverer, e.g. apply(f, (x, y) + t)
        # can be translated into f(x, y, *t) instead of f(*(x, y) + t)
        new = pytree.Node(syms.power,
                          (func,
                           pytree.Node(syms.trailer,
                                       (pytree.Leaf(token.LPAR, "("),
                                        pytree.Node(syms.arglist, l_newargs),
                                        pytree.Leaf(token.RPAR, ")")))))
        new.set_prefix(prefix)
        return new
