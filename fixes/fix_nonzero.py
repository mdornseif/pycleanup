"""Fixer for __nonzero__ -> __bool__ methods."""
# Author: Collin Winter

# Local imports
import pytree
from pgen2 import token
from pygram import python_symbols as syms
from fixes import basefix
from fixes.macros import Name

class FixNonzero(basefix.BaseFix):
    PATTERN = """
    classdef< 'class' any+ ':'
              suite< any*
                     funcdef< 'def' name='__nonzero__'
                              parameters< '(' NAME ')' > any+ >
                     any* > >
    """
    
    def transform(self, node):
        results = self.match(node)
        assert results

        name = results["name"]
        new = Name("__bool__")
        new.set_prefix(name.get_prefix())
        name.replace(new)
