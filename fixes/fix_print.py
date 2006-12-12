# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Null fixer.  Use as a template."""


class FixNull(object):

    """Fixer class.

    The class name must be FixFooBar where FooBar is the result of
    removing underscores and capitalizing the words of the fix name.
    For example, the class name for a fixer named 'has_key' should be
    FixHasKey.
    """

    def __init__(self, options):
        """Initializer.

        The argument is an optparse.Values instance which can be used
        to inspect the command line options.
        """
        self.options = options

    def match(self, node):
        """Matcher.

        Should return a true or false object (not necessarily a bool).
        It may return a non-empty dict of matching sub-nodes as
        returned by a matching pattern.
        """
        return None

    def transform(self, node):
        """Transformer.

        Should return None, or a node that is a modified copy of the
        argument node.  The argument should not be modified in place.
        """
        return None
