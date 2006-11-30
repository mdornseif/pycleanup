#!/usr/bin/env python2.5
# Copyright 2006 Google Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Refactoring tool: change 'x.has_key(y)' into 'y in x'."""

__author__ = "Guido van Rossum <guido@python.org>"

# Python imports
import os
import sys
import logging

import pgen2
from pgen2 import driver

import pynode

logging.basicConfig(level=logging.WARN)

def main():
    args = sys.argv[1:] or ["example.py"]

    gr = driver.load_grammar("Grammar.txt")
    dr = driver.Driver(gr, convert=pynode.convert)

    for fn in args:
        print "Parsing", fn
        tree = dr.parse_file(fn)
        tree.set_parents()
        refactor(tree)
        diff(fn, tree)

def refactor(tree):
    visit(tree, fix_has_key)

def visit(node, func):
    func(node)
    for child in node.get_children():
        visit(child, func)

# Sample nodes
_context = ("", (0, 0))
n_dot = pynode.Token(_context, ".")
n_has_key = pynode.Name(_context, "has_key")
n_trailer_has_key = pynode.trailer(_context, n_dot, n_has_key)
n_lpar = pynode.Token(_context, "(")
n_star = pynode.Token(_context, "*")
n_comma = pynode.Token(_context, ",")
n_in = pynode.Token((" ", (0, 0)), "in")

def fix_has_key(node):
    if node != n_trailer_has_key:
        return
    # XXX Could use more DOM manipulation primitives and matching operations
    parent = node.parent
    nodes = parent.get_children()
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
    if not isinstance(next, pynode.trailer):
        return # ".has_key" not followed by another trailer
    next_children = next.get_children()
    if next_children[0] != n_lpar:
        return # ".has_key" not followed by "(...)"
    if len(next_children) != 3:
        return # ".has_key" followed by "()"
    argsnode = next_children[1]
    arg = argsnode
    if isinstance(argsnode, pynode.arglist):
        args = argsnode.get_children()
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
    new = pynode.comparison(_context,
                            arg,
                            n_in,
                            pynode.power(_context, *nodes[:i]))
    # XXX Sometimes we need to parenthesize arg or new.  Later.
    parent.parent.replace(parent, new)

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
