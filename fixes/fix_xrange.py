# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that changes xrange(...) into range(...)."""

# Local imports
from fixes import basefix
from fixes.util import Name

class FixXrange(basefix.BaseFix):

    PATTERN = """
              power< name='xrange' trailer< '(' [any] ')' > >
              """

    def transform(self, node, results):
        name = results["name"]
        name.replace(Name("range", prefix=name.get_prefix()))
