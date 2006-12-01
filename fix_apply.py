#!/usr/bin/env python2.5
# Copyright 2006 Google Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Refactoring tool: change 'x.has_key(y)' into 'y in x'."""

__author__ = "Guido van Rossum <guido@python.org>"

# Python imports
import os
import sys
import token
import logging

import pgen2
from pgen2 import driver

import pytree

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


# Constant nodes
n_apply = pytree.Node(syms.atom, [pytree.Leaf(token.NAME, "apply")])
n_lpar = pytree.Leaf(token.LPAR, "(")
n_rpar = pytree.Leaf(token.RPAR, ")")
n_comma = pytree.Leaf(token.COMMA, ",")
n_star = pytree.Leaf(token.STAR, "*")
n_doublestar = pytree.Leaf(token.DOUBLESTAR, "**")


def fix_apply(node):
    if not (node.type == syms.power and
            len(node.children) >= 2 and
            node.children[0] == n_apply and
            node.children[1].type == syms.trailer and
            node.children[1].children[0] == n_lpar):
        return
    n_arglist = node.children[1].children[1]
    if n_arglist == n_rpar:
        return # apply() with no arguments?!
    l_args = []
    for arg in n_arglist.children:
        if arg == n_comma:
            continue
        if arg == n_star or arg == n_doublestar:
            return # apply() with a * or ** in its argument list?!
        arg.set_prefix("")
        l_args.append(arg)
    if not 2 <= len(l_args) <= 3:
        return # too few or too many arguments to handle
    prefix = node.get_prefix()
    l_args[0].replace(None)
    node.children[0].replace(l_args[0])
    node.set_prefix(prefix)
    l_newargs = [pytree.Leaf(token.STAR, "*"), l_args[1]]
    if l_args[2:]:
        l_newargs.extend([pytree.Leaf(token.COMMA, ","),
                          pytree.Leaf(token.DOUBLESTAR, "**"),
                          l_args[2]])
        l_newargs[-2].set_prefix(" ")
    n_arglist.replace(pytree.Node(syms.arglist, l_newargs))
    # XXX Sometimes we can be cleverer, e.g. apply(f, (x, y) + t)
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
