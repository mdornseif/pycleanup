# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for callable().

This converts callable(obj) into hasattr(obj, '__call__')."""

# Local imports
import pytree
from fixes import basefix
from fixes.util import Call, Name, String

class FixCallable(basefix.BaseFix):

    # XXX(nnorwitz): need to ignore: callable(*args)
    # XXX(nnorwitz): or use of keywords, it could signify doing a callback,
    # not using the builtin callable().
    PATTERN = """
      power< 'callable' trailer< '(' func=any ')' > >
    """

    def transform(self, node):
        results = self.match(node)
        func = results["func"]

        args = [func.clone(), String(', '), String("'__call__'")]
        new = Call(Name("hasattr"), args)
        new.set_prefix(node.get_prefix())
        return new

