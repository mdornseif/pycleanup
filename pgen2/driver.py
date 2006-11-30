# Copyright 2004-2005 Elemental Security, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

# Modifications:
# Copyright 2006 Python Software Foundation. All Rights Reserved.

"""Parser driver.

This provides a high-level interface to parse a file into a syntax tree.

"""

__author__ = "Guido van Rossum <guido@python.org>"

__all__ = ["Driver", "load_grammar"]

# Python imports
import os
import token
import logging
import tokenize

# Pgen imports
from pgen2 import parse
from pgen2 import astnode
from pgen2 import grammar

class Driver(object):

    def __init__(self, grammar, convert=None, logger=None):
        self.grammar = grammar
        if logger is None:
            logger = logging.getLogger()
        self.logger = logger
        self.convert = convert
 
    def parse_stream_raw(self, stream, debug=False):
        """Parse a stream and return the concrete syntax tree."""
        p = parse.Parser(self.grammar, self.convert)
        p.setup()
        lineno = 1
        column = 0
        type = value = start = end = line_text = None
        prefix = ""
        for quintuple in tokenize.generate_tokens(stream.readline):
            type, value, start, end, line_text = quintuple
            if start != (lineno, column):
                assert (lineno, column) <= start, ((lineno, column), start)
                s_lineno, s_column = start
                if lineno < s_lineno:
                    prefix += "\n" * (s_lineno - lineno)
                    lineno = s_lineno
                    column = 0
                if column < s_column:
                    prefix += " " * (s_column - column)
                    column = s_column
            if type in (tokenize.COMMENT, tokenize.NL):
                prefix += value
                lineno, column = end
                if value.endswith("\n"):
                    lineno += 1
                    column = 0
                continue
            if type == token.OP:
                type = grammar.opmap[value]
            if debug:
                self.logger.debug("%s %r", token.tok_name[type], value)
            if p.addtoken(type, value, (prefix, start)):
                if debug:
                    self.logger.debug("Stop.")
                break
            prefix = ""
            lineno, column = end
            if value.endswith("\n"):
                lineno += 1
                column = 0
        else:
            # We never broke out -- EOF is too soon (how can this happen???)
            raise parse.ParseError("incomplete input", t, v, x)
        return p.rootnode

    def parse_stream(self, stream, debug=False):
        """Parse a stream and return the syntax tree."""
        return self.parse_stream_raw(stream, debug)

    def parse_file(self, filename, debug=False):
        """Parse a file and return the syntax tree."""
        stream = open(filename)
        try:
            return self.parse_stream(stream, debug)
        finally:
            stream.close()

    def parse_string(self, text, debug=False):
        """Parse a string and return the syntax tree."""
        from StringIO import StringIO
        stream = StringIO(text)
        return self.parse_stream(stream, debug)

def load_grammar(gt="Grammar.txt", gp=None,
                 save=True, force=False, logger=None):
    """Load the grammar (maybe from a pickle)."""
    if logger is None:
        logger = logging.getLogger()
    if gp is None:
        head, tail = os.path.splitext(gt)
        if tail == ".txt":
            tail = ""
        gp = head + tail + ".pickle"
    if force or not _newer(gp, gt):
        logger.info("Generating grammar tables from %s", gt)
        from pgen2 import pgen
        g = pgen.generate_grammar(gt)
        if save:
            logger.info("Writing grammar tables to %s", gp)
            g.dump(gp)
    else:
        g = grammar.Grammar()
        g.load(gp)
    return g

def _newer(a, b):
    """Inquire whether file a was written since file b."""
    if not os.path.exists(a):
        return False
    if not os.path.exists(b):
        return True
    return os.path.getmtime(a) >= os.path.getmtime(b)
