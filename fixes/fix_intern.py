# Copyright 2006 Georg Brandl.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for intern()."""

# Python imports
import token

# Local imports
import pytree
import patcomp
import pygram

syms = pygram.python_symbols
pat_compile = patcomp.PatternCompiler().compile_pattern

PATTERN = """
power< 'intern'
       trailer< lpar='('
                ( not(arglist | argument<any '=' any>) obj=any
                  | obj=arglist<(not argument<any '=' any>) any ','> )
                rpar=')' >
       after=any*
>
"""


class FixIntern(object):

    def __init__(self, options):
        self.options = options
        self.pattern = pat_compile(PATTERN)

    def match(self, node):
        results = {}
        return self.pattern.match(node, results) and results

    def transform(self, node):
        results = self.match(node)
        assert results
        obj = results["obj"].clone()
        if obj.type == syms.arglist:
            newarglist = obj.clone()
        else:
            newarglist = pytree.Node(syms.arglist, [obj.clone()])
        after = results["after"]
        if after:
            after = tuple(n.clone() for n in after)
        new = pytree.Node(syms.power,
                          (pytree.Leaf(token.NAME, "sys"),
                           pytree.Node(syms.trailer,
                                       [pytree.Leaf(token.DOT, "."),
                                        pytree.Leaf(token.NAME, "intern")]),
                           pytree.Node(syms.trailer,
                                       [results["lpar"].clone(),
                                        newarglist,
                                        results["rpar"].clone()]))
                          + after)
        new.set_prefix(node.get_prefix())
        return new
                
