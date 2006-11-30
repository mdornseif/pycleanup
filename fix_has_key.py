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

syms = Symbols(gr)

def main():
    args = sys.argv[1:] or ["example.py"]

    dr = driver.Driver(gr, convert=pytree.convert)

    for fn in args:
        print "Parsing", fn
        tree = dr.parse_file(fn)
        refactor(tree)
        diff(fn, tree)

def refactor(tree):
    visit(tree, fix_has_key)

def visit(node, func):
    func(node)
    for child in node.children:
        visit(child, func)

# Sample nodes
n_dot = pytree.Leaf(token.DOT, ".")
n_has_key = pytree.Leaf(token.NAME, "has_key")
n_trailer_has_key = pytree.Node(syms.trailer, (n_dot, n_has_key))
n_lpar = pytree.Leaf(token.LPAR, "(")
n_star = pytree.Leaf(token.STAR, "*")
n_comma = pytree.Leaf(token.COMMA, ",")
n_in = pytree.Leaf(token.NAME, "in", context=(" ", (0, 0)))

import pdb

def fix_has_key(node):
    if node != n_trailer_has_key:
        return
    # XXX Could use more DOM manipulation primitives and matching operations
    parent = node.parent
    nodes = parent.children
    for i, n in enumerate(nodes):
        if n is node:
            break
    else:
        print "Can't find node in parent?!"
        return
    if i+1 >= len(nodes):
        return # Nothing follows ".has_key"
    if len(nodes) != i+2:
        return # Too much follows ".has_key", e.g. ".has_key(x).blah"
    next = nodes[i+1]
    if next.type != syms.trailer:
        return # ".has_key" not followed by another trailer
    next_children = next.children
    if next_children[0] != n_lpar:
        return # ".has_key" not followed by "(...)"
    if len(next_children) != 3:
        return # ".has_key" followed by "()"
    argsnode = next_children[1]
    arg = argsnode
    if argsnode.type != syms.arglist:
        args = argsnode.children
        if len(args) > 2:
            return # Too many arguments
        if len(args) == 2:
            if args[0] == n_star:
                return # .has_key(*foo) -- you've gotta be kidding!
            if args[1] != n_comma:
                return # Only .has_key(foo,) expected
        arg = args[0]
    # Change "X.has_key(Y)" into "Y in X"
    arg.set_prefix(nodes[0].get_prefix())
    nodes[0].set_prefix(" ")
    new = pytree.Node(syms.comparison,
                      (arg, n_in, pytree.Node(syms.power, nodes[:i])))
    # XXX Sometimes we need to parenthesize arg or new.  Later.
    parent.replace(new)

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
