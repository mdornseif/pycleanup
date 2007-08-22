# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for removing uses of the types module.

These work for only the known names in the types module.  The forms above
can include types. or not.  ie, It is assumed the module is imported either as:

    import types
    from types import ... # either * or specific types

The import statements are not modified.

There should be another fixer that handles at least the following constants:

   type([]) -> list
   type(()) -> tuple
   type('') -> str

"""

# Local imports
from pgen2 import token
from fixes import basefix
from fixes.util import Name

_TYPE_MAPPING = {
        'DictType': 'dict',
        'ListType': 'list',
        'NoneType': 'type(None)',
        'IntType': 'int',
        'LongType': 'int',
        'FloatType': 'float',
        'StringType': 'str',
        'TupleType': 'tuple',
        'UnicodeType': 'unicode',
    }

_pats = ["power< 'types' trailer< '.' name='%s' > >" % t for t in _TYPE_MAPPING]

class FixTypes(basefix.BaseFix):

    PATTERN = '|'.join(_pats)

    def transform(self, node, results):
        new_value = _TYPE_MAPPING.get(results["name"].value)
        if new_value:
            return Name(new_value, prefix=node.get_prefix())
        return None
