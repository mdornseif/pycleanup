#!/usr/bin/env python2.5
# Copyright 2006 Python Software Foundation. All Rights Reserved.

"""XXX."""

##from __future__ import with_statement

__author__ = "Guido van Rossum <guido@python.org>"

# Python imports
import os
import sys
import logging

import pgen2
from pgen2 import driver

import pynode

logging.basicConfig(level=logging.WARN)

def diff(fn, tree):
    f = open("@", "w")
    try:
        f.write(str(tree))
    finally:
        f.close()
    return os.system("diff -u %s @" % fn)

def main():
    gr = driver.load_grammar("Grammar.txt")
    dr = driver.Driver(gr, convert=pynode.convert)

    tree = dr.parse_file("example.py", debug=True)
    sys.stdout.write(str(tree))
    return

    # Process every imported module
    for name in sys.modules:
        mod = sys.modules[name]
        if mod is None or not hasattr(mod, "__file__"):
            continue
        fn = mod.__file__
        if fn.endswith(".pyc"):
            fn = fn[:-1]
        if not fn.endswith(".py"):
            continue
        print >>sys.stderr, "Parsing", fn
        tree = dr.parse_file(fn, debug=True)
        diff(fn, tree)

    # Process every single module on sys.path (but not in packages)
    for dir in sys.path:
        try:
            names = os.listdir(dir)
        except os.error:
            continue
        print >>sys.stderr, "Scanning", dir, "..."
        for name in names:
            if not name.endswith(".py"):
                continue
            print >>sys.stderr, "Parsing", name
            fn = os.path.join(dir, name)
            try:
                tree = dr.parse_file(fn, debug=True)
            except pgen2.parse.ParseError, err:
                print "ParseError:", err
            else:
                diff(fn, tree)

if __name__ == "__main__":
    main()
