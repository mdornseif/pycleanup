#!/usr/bin/env python2.5
# Copyright 2006 Google Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Refactoring tool: change print statements into function calls, ie change:
    'print ...'	     into 'Print(...)'
    'print ... ,'    into 'Print(..., sep=" ", end="")'
    'print >>x, ...' into 'Print(..., file=x)'
"""

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
    visit(tree, fix_print)


def visit(node, func):
    func(node)
    for child in node.children:
        visit(child, func)


def fix_print(node):
    if node.type != syms.print_stmt:
        return
    assert node.children[0] == pytree.Leaf(token.NAME, "print")
    args = node.children[1:]
    sep = end = file = None
    if args and args[-1] == pytree.Leaf(token.COMMA, ","):
        args = args[:-1]
        sep = " "
        end = ""
    if args and args[0] == pytree.Leaf(token.RIGHTSHIFT, ">>"):
        assert len(args) >= 2
        file = args[1]
        args = args[3:] # Strip a possible comma after the file expression
    # Now synthesize a Print(args, sep=..., end=..., file=...) node.
    n_print = pytree.Leaf(token.NAME, "Print") # XXX -> "print"
    l_args = list(args)
    if l_args:
        l_args[0].set_prefix("")
    if sep is not None or end is not None or file is not None:
        if sep is not None:
            add_kwarg(l_args, "sep",
                      pytree.Leaf(token.STRING, repr(sep)))
        if end is not None:
            add_kwarg(l_args, "end",
                      pytree.Leaf(token.STRING, repr(end)))
        if file is not None:
            add_kwarg(l_args, "file", file)
    if l_args:
        n_arglist = pytree.Node(syms.arglist, l_args)
    else:
        n_arglist = None
    l_args = [pytree.Leaf(token.LPAR, "("), pytree.Leaf(token.RPAR, ")")]
    if n_arglist:
        l_args.insert(1, n_arglist)
    n_trailer = pytree.Node(syms.trailer, l_args)
    n_stmt = pytree.Node(syms.power, (n_print, n_trailer))
    n_stmt.set_prefix(node.get_prefix())
    node.replace(n_stmt)


def add_kwarg(l_nodes, s_kwd, n_expr):
    # XXX All this prefix-setting may lose comments (though rarely)
    n_expr.set_prefix("")
    n_argument = pytree.Node(syms.argument,
                             (pytree.Leaf(token.NAME, s_kwd),
                              pytree.Leaf(token.EQUAL, "="),
                              n_expr))
    if l_nodes:
        l_nodes.append(pytree.Leaf(token.COMMA, ","))
        n_argument.set_prefix(" ")
    l_nodes.append(n_argument)


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
