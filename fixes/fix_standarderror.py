# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for StandardError -> Exception."""

# Local imports
from fixes import basefix
from fixes.util import Name


class FixStandarderror(basefix.BaseFix):

    PATTERN = """
              'StandardError'
              """

    def transform(self, node, results):
        return Name("Exception", prefix=node.get_prefix())
