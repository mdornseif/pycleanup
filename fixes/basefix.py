# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Base class for fixers (optional, but recommended)."""

# Python imports
import logging
import itertools

# Local imports
import patcomp
import pygram

# For new_name()
numbers = itertools.count(1)

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
    used_names = set() # A set of all used NAMEs

    # Shortcut for access to Python grammar symbols
    syms = pygram.python_symbols

    def __init__(self, options):
        """Initializer.  Subclass may override.

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
        results = {"node": node}
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

    def new_name(self, template="xxx_todo_changeme"):
        name = template
        while name in self.used_names:
            name = template + str(numbers.next())
        self.used_names.add(name)
        return name

    def cannot_convert(self, node, reason=None):
        lineno = node.get_lineno()
        for_output = node.clone()
        for_output.set_prefix("")
        msg = "At line %d: could not convert: %s"
        self.logger.warning(msg % (lineno, for_output))
        if reason:
            self.logger.warning(reason)
