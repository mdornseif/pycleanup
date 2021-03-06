"""Fixer for __nonzero__ -> __bool__ methods."""
# Author: Collin Winter

# Local imports
from .. import fixer_base
from ..fixer_util import Name, syms

class FixNonzero(fixer_base.BaseFix):
    PATTERN = """
    classdef< 'class' any+ ':'
              suite< any*
                     funcdef< 'def' name='__nonzero__'
                              parameters< '(' NAME ')' > any+ >
                     any* > >
    """
    explicit = True # The user must ask for this fixers

    def transform(self, node, results):
        name = results["name"]
        new = Name(u"__bool__", prefix=name.prefix)
        name.replace(new)
