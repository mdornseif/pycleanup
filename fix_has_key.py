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
import patcomp

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
n_star = pytree.Leaf(token.STAR, "*")
n_comma = pytree.Leaf(token.COMMA, ",")

# Tree matching pattern
pat_compile = patcomp.PatternCompiler().compile_pattern
p_has_key = pat_compile("""
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
""")

def fix_has_key(node):
    results = {}
    if not p_has_key.match(node, results):
        return
    prefix = node.get_prefix()
    before = results["before"]
    arg = results["arg"]
    after = results["after"]
    arg.replace(None)
    if arg.type in (syms.comparison, syms.not_test, syms.and_test,
                    syms.or_test, syms.test, syms.lambdef, syms.argument):
        arg = parenthesize(arg)
    for n in before:
        n.replace(None)
    if len(before) == 1:
        before = before[0]
    else:
        before = pytree.Node(syms.power, before)
    before.set_prefix(" ")
    n_in = pytree.Leaf(token.NAME, "in")
    n_in.set_prefix(" ")
    new = pytree.Node(syms.comparison, (arg, n_in, before))
    if after:
        for n in after:
            n.replace(None)
        new = parenthesize(new)
        new = pytree.Node(syms.power, (new,) + tuple(after))
    if node.parent.type in (syms.comparison, syms.expr, syms.xor_expr,
                            syms.and_expr, syms.shift_expr, syms.arith_expr,
                            syms.term, syms.factor, syms.power):
        new = parenthesize(new)
    new.set_prefix(prefix)
    node.replace(new)

def parenthesize(node):
    return pytree.Node(syms.atom,
                       (pytree.Leaf(token.LPAR, "("),
                        node,
                        pytree.Leaf(token.RPAR, ")")))


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
