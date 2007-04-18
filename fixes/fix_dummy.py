# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""This is a pass-through fixer. It can be useful when changing certain
parts of the parser or pytree."""

# Local imports
from fixes import basefix

class FixDummy(basefix.BaseFix):

    def match(self, node):
        return True

    def transform(self, node):
        node.changed()
