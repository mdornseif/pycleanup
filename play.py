#!/usr/bin/env python2.5
# Copyright 2006 Python Software Foundation. All Rights Reserved.

"""XXX."""

from __future__ import with_statement

__author__ = "Guido van Rossum <guido@python.org>"

# Python imports
import os
import sys
import logging

import pgen2
from pgen2 import driver

import pynode

logging.basicConfig(level=logging.INFO)

SAMPLE = """\
for i in range(10):
    print i
class C(object, list):
    def f(a, b, c=1, *args, **kwds):
        pass
"""

def main():
    gr = driver.load_grammar("Grammar.txt")
    dr = driver.Driver(gr, convert=pynode.convert)

##     tree = dr.parse_file("pynode.py", debug=True)
##     print tree

##     for name in sys.modules:
##         mod = sys.modules[name]
##         if mod is None or not hasattr(mod, "__file__"):
##             continue
##         fn = mod.__file__
##         if fn.endswith(".pyc"):
##             fn = fn[:-1]
##         if not fn.endswith(".py"):
##             continue
##         print >>sys.stderr, "Parsing", fn
##         dr.parse_file(fn, debug=True)

    for dir in reversed(sys.path):
        try:
            names = os.listdir(dir)
        except os.error:
            continue
        print >>sys.stderr, "Scanning", dir, "..."
        for name in names:
            if not name.endswith(".py"):
                continue
            print >>sys.stderr, "Parsing", name
            try:
                dr.parse_file(os.path.join(dir, name), debug=True)
            except pgen2.parse.ParseError, err:
                print "ParseError:", err
        

if __name__ == "__main__":
    main()
