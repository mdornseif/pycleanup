# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that changes buffer(...) into memoryview(...)."""

# Local imports
from fixes import basefix
from fixes.util import Name


class FixBuffer(basefix.BaseFix):

    explicit = True # The user must ask for this fixer

    PATTERN = """
              power< name='buffer' trailer< '(' [any] ')' > >
              """

    def transform(self, node, results):
        name = results["name"]
        name.replace(Name("memoryview", prefix=name.get_prefix()))
