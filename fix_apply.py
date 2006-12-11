#!/usr/bin/env python2.5
# Copyright 2006 Google Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Refactoring tool: change apply(f, a, kw) into f(*a, **kw)."""

__author__ = "Guido van Rossum <guido@python.org>"

# Python imports
import os
import sys
import token
import logging

import pgen2
from pgen2 import driver

import pytree
import patcomp

logging.basicConfig(level=logging.DEBUG)

gr = driver.load_grammar("Grammar.txt") # used by node initializers


class Symbols(object):

    def __init__(self, gr):
        for name, symbol in gr.symbol2number.iteritems():
            setattr(self, name, symbol)


# XXX Make this importable as a module
syms = Symbols(gr)


# XXX Write a single driver script that can do any (or all) refactorings
def main():
    args = sys.argv[1:] or ["example.py"]

    dr = driver.Driver(gr, convert=pytree.convert)

    for fn in args:
        print "Parsing", fn
        tree = dr.parse_file(fn)
        refactor(tree)
        diff(fn, tree)


def refactor(tree):
    visit(tree, fix_apply)


def visit(node, func):
    func(node)
    for child in node.children:
        visit(child, func)


# Constant nodes used for matching
n_comma = pytree.Leaf(token.COMMA, ",")
n_star = pytree.Leaf(token.STAR, "*")
n_doublestar = pytree.Leaf(token.DOUBLESTAR, "**")

# Tree matching patterns
pat_compile = patcomp.PatternCompiler().compile_pattern
p_apply = pat_compile("""
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
    )


def fix_apply(node):
    results = {}
    if not p_apply.match(node, results):
        return
    n_arglist = node.children[1].children[1]
    assert n_arglist.type
    func = results["func"]
    args = results["args"]
    kwds = results.get("kwds")
    prefix = node.get_prefix()
    func.replace(None)
    if (func.type not in (token.NAME, syms.atom) and
        (func.type != syms.power or
         func.children[-2].type == token.DOUBLESTAR)):
        # Need to parenthesize
        func = pytree.Node(syms.atom,
                           (pytree.Leaf(token.LPAR, "("),
                            func,
                            pytree.Leaf(token.RPAR, ")")))
    func.set_prefix("")
    args.replace(None)
    args.set_prefix("")
    if kwds is not None:
        kwds.replace(None)
        kwds.set_prefix("")
    node.children[0].replace(func)
    node.set_prefix(prefix)
    l_newargs = [pytree.Leaf(token.STAR, "*"), args]
    if kwds is not None:
        l_newargs.extend([pytree.Leaf(token.COMMA, ","),
                          pytree.Leaf(token.DOUBLESTAR, "**"),
                          kwds])
        l_newargs[-2].set_prefix(" ") # that's the ** token
    for n in l_newargs:
        if n.parent is not None:
            n.replace(None) # Force parent to None
    n_arglist.replace(pytree.Node(syms.arglist, l_newargs))
    # XXX Sometimes we could be cleverer, e.g. apply(f, (x, y) + t)
    # can be translated into f(x, y, *t) instead of f(*(x, y) + t)


def diff(fn, tree):
    f = open("@", "w")
    try:
        f.write(str(tree))
    finally:
        f.close()
    try:
        return os.system("diff -u %s @" % fn)
    finally:
        os.remove("@")


if __name__ == "__main__":
    main()
