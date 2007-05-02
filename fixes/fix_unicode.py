"""Fixer that changes unicode to str and u"..." into "...".

"""

import re
import pytree
from pgen2 import token
from fixes import basefix

class FixUnicode(basefix.BaseFix):

  PATTERN = "STRING | NAME<'unicode'>"

  def transform(self, node):
    if node.type == token.NAME:
      if node.value == "unicode":
        new = node.clone()
        new.value = "str"
        return new
      # XXX Warn when __unicode__ found?
    elif node.type == token.STRING:
      if re.match(r"[uU][rR]?[\'\"]", node.value):
        new = node.clone()
        new.value = new.value[1:]
        return new
    return None
