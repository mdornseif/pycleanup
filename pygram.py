# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Export the Python grammar and symbols."""

from pgen2 import driver


class Symbols(object):

    def __init__(self, gr):
        for name, symbol in gr.symbol2number.iteritems():
            setattr(self, name, symbol)


python_grammar = driver.load_grammar("Grammar.txt")
python_symbols = Symbols(python_grammar)
