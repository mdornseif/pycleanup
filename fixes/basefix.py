# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Base class for fixers (optional, but recommended)."""

# Local imports
import patcomp
import pygram


class BaseFix(object):

    """Optional base class for fixers."""

    PATTERN = None  # Subclass *must* override with a string literal
    pattern = None  # Compiled pattern, set by compile_pattern()
    options = None  # Options object passed to initializer

    # Shortcut for access to Python grammar symbols
    syms = pygram.python_symbols

    def __init__(self, options):
        """Initializer.  Subclass may override."""
        self.options = options
        self.compile_pattern()

    def compile_pattern(self):
        """Compiles self.PATTERN into self.pattern.

        Subclass may override if it doesn't want to use
        self.{pattern,PATTERN} in .match().
        """
        self.pattern = patcomp.PatternCompiler().compile_pattern(self.PATTERN)

    def match(self, node):
        """Returns match for a given parse tree node.

        Subclass may override.
        """
        results = {}
        return self.pattern.match(node, results) and results

    def transform(self, node):
        """Returns the transformation for a given parse tree node.

        Subclass must override.
        """
        return None

    def parenthesize(self, node):
        """Wrapper around pygram.parenthesize()."""
        return pygram.parenthesize(node)
