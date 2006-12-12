# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for apply()."""

# Python imports
import token

# Local imports
import pytree
import patcomp
import pygram

syms = pygram.python_symbols
pat_compile = patcomp.PatternCompiler().compile_pattern

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


class FixApply(object):

    def __init__(self, options):
        self.options = options
        self.pattern = pat_compile(PATTERN)

    def match(self, node):
        results = {}
        return self.pattern.match(node, results) and results

    def transform(self, node):
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
            func = pygram.parenthesize(func)
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
