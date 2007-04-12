"""Fixer that turns 1L into 1, 0755 into 0o755,
0XABC into 0xABC, 1E5 into 1e5, 1J into 1j.
"""
# Copyright 2007 Georg Brandl.
# Licensed to PSF under a Contributor Agreement.

# Local imports
from pgen2 import token
from fixes import basefix
from fixes.util import Number, set


class FixNumliterals(basefix.BaseFix):
    # This is so simple that we don't need the pattern compiler.

    def match(self, node):
        # Override
        return (node.type == token.NUMBER and
                (node.value.startswith("0") or
                 'E' in node.value or
                 'J' in node.value or
                 node.value[-1] in "Ll"))

    def transform(self, node):
        val = node.value
        if val[-1] in 'Ll':
            val = val[:-1]
        if 'J' in val:
            val = val.replace('J', 'j')
        if 'E' in val:
            val = val.replace('E', 'e')
        if val.startswith('0X'):
            val = '0x' + val[2:]
        elif val.startswith('0') and val.isdigit() and len(set(val)) > 1:
            val = "0o" + val[1:]

        return Number(val, prefix=node.get_prefix())
