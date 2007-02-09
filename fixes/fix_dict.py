# Copyright 2007 Google, Inc. All Rights Reserved.

"""Fixer for dict methods.

d.keys() -> list(d.keys())
d.items() -> list(d.items())
d.values() -> list(d.values())

d.iterkeys() -> iter(d.keys())
d.iteritems() -> iter(d.items())
d.itervalues() -> iter(d.values())

Except in certain very specific contexts: the iter() can be dropped
when the context is list(), sorted(), iter() or for...in; the list()
can be dropped when the context is list() or sorted() (but not iter()
or for...in!).

Note: iter(d.keys()) could be written as iter(d) but since the
original d.iterkeys() was also redundant we don't fix this.  And there
are (rare) contexts where it makes a difference (e.g. when passing it
as an argument to a function that introspects the argument).
"""

# Python imports
import token

# Local imports
import pytree
import patcomp
from fixes import basefix
from fixes import macros

class FixDict(basefix.BaseFix):

  PATTERN = """
  power< prefix=any+
         trailer< '.' method=('keys'|'items'|'values'|
                              'iterkeys'|'iteritems'|'itervalues') >
         trailer< '(' ')' >
         tail=any*
  >
  """

  def transform(self, node):
    results = self.match(node)
    prefix = results["prefix"]
    method = results["method"][0].value # Extract method name
    tail = results["tail"]
    if tail:
      return self.cannot_convert(node,
                                 "stuff after .[iter]keys() etc. unsupported")
    syms = self.syms
    isiter = method.startswith("iter")
    if isiter:
      method = method[4:]
    assert method in ("keys", "items", "values"), repr(method)
    prefix = [n.clone() for n in prefix]
    new = pytree.Node(syms.power,
                      prefix + [pytree.Node(syms.trailer,
                                            [pytree.Leaf(token.DOT, '.'),
                                             macros.Name(method)]),
                                pytree.Node(syms.trailer,
                                            [macros.lparen_leaf.clone(),
                                             macros.rparen_leaf.clone()])])
    if not self.in_special_context(node, isiter):
      new.set_prefix("")
      new = macros.Call(macros.Name(isiter and "iter" or "list"), [new])
    new.set_prefix(node.get_prefix())
    return new

  P1 = "trailer< '(' node=any ')' >"
  p1 = patcomp.PatternCompiler().compile_pattern(P1)

  P2 = "power< func=NAME trailer< '(' node=any ')' > any* >"
  p2 = patcomp.PatternCompiler().compile_pattern(P2)

  def in_special_context(self, node, isiter):
    results = {}
    if not (self.p1.match(node.parent, results) and
            results["node"] is node):
      return False
    results = {}
    if not (self.p2.match(node.parent.parent, results) and
            results["node"] is node):
      return False
    if isiter:
      return results["func"].value == ("iter", "list", "sorted")
    else:
      return results["func"].value in ("list", "sorted")
    # XXX TODO: for...in context.
