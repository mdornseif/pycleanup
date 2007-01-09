# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Base class for fixers (optional, but recommended)."""

# Python imports
import logging

# Local imports
import patcomp
import pygram


class BaseFix(object):

    """Optional base class for fixers.

    The subclass name must be FixFooBar where FooBar is the result of
    removing underscores and capitalizing the words of the fix name.
    For example, the class name for a fixer named 'has_key' should be
    FixHasKey.
    """

    PATTERN = None  # Subclass *must* override with a string literal
    pattern = None  # Compiled pattern, set by compile_pattern()
    options = None  # Options object passed to initializer
    filename = None # The filename (set by set_filename)
    logger = None   # A logger (set by set_filename)

    # Shortcut for access to Python grammar symbols
    syms = pygram.python_symbols

    def __init__(self, options):
        """Initializer.  Subclass may override.
o
        The argument is an optparse.Values instance which can be used
        to inspect the command line options.
        """
        self.options = options
        self.compile_pattern()

    def compile_pattern(self):
        """Compiles self.PATTERN into self.pattern.

        Subclass may override if it doesn't want to use
        self.{pattern,PATTERN} in .match().
        """
        self.pattern = patcomp.PatternCompiler().compile_pattern(self.PATTERN)

    def set_filename(self, filename):
        """Set the filename, and a logger derived from it.

        The main refactoring tool should call this.
        """
        self.filename = filename
        self.logger = logging.getLogger(filename)

    def match(self, node):
        """Returns match for a given parse tree node.

        Should return a true or false object (not necessarily a bool).
        It may return a non-empty dict of matching sub-nodes as
        returned by a matching pattern.

        Subclass may override.
        """
        results = {}
        return self.pattern.match(node, results) and results

    def transform(self, node):
        """Returns the transformation for a given parse tree node.

        Should return None, or a node that is a modified copy of the
        argument node.  The argument should not be modified in place.

        Subclass *must* override.
        """
        return None

    def parenthesize(self, node):
        """Wrapper around pygram.parenthesize()."""
        return pygram.parenthesize(node)
