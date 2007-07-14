"""Fixer that changes raw_input(...) into input(...)."""
# Author: Andre Roberge

# Local imports
from fixes import basefix
from fixes.util import Name

class FixRawInput(basefix.BaseFix):

    PATTERN = """
              power< name='raw_input' trailer< '(' [any] ')' > >
              """

    def transform(self, node, results):
        name = results["name"]
        name.replace(Name("input", prefix=name.get_prefix()))
