# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that changes map(F, ...) into list(map(F, ...)).

As a special case, map(None, X) is changed into list(X).  (This is
necessary because the semantics are changed in this case -- the new
map(None, X) is equivalent to [(x,) for x in X].)

We avoid the transformation (except for the special case mentioned
above) if the map() call is directly contained in iter(<>), list(<>),
tuple(<>), sorted(<>), ...join(<>), or for V in <>:.

NOTE: This is still not correct if the original code was depending on
map(F, X, Y, ...) to go on until the longest argument is exhausted,
substituting None for missing values -- like zip(), it now stops as
soon as the shortest argument is exhausted.
"""

# Local imports
import pytree
import patcomp
from pgen2 import token
from fixes import basefix
from fixes.util import Name, Call, ListComp, attr_chain
from pygram import python_symbols as syms

class FixMap(basefix.BaseFix):

    PATTERN = """
    map_none=power<
        'map'
        trailer< '(' arglist< 'None' ',' arg=any [','] > ')' >
    >
    |
    map_lambda=power<
        'map'
        trailer<
            '('
            arglist<
                lambdef< 'lambda' fp=NAME ':' xp=any >
                ','
                it=any
            >
            ')'
        >
    >
    |
    power<
        'map'
        args=trailer< '(' [any] ')' >
    >
    """

    def transform(self, node, results):
        if "map_lambda" in results:
            new = ListComp(results.get("xp").clone(),
                           results.get("fp").clone(),
                           results.get("it").clone())
        else:
            if "map_none" in results:
                new = results["arg"].clone()
            else:
                if in_special_context(node):
                    return None
                new = node.clone()
            new.set_prefix("")
            new = Call(Name("list"), [new])
        new.set_prefix(node.get_prefix())
        return new

P0 = """for_stmt< 'for' any 'in' node=any ':' any* >
        | comp_for< 'for' any 'in' node=any any* >
     """
p0 = patcomp.compile_pattern(P0)

P1 = """
power<
    ( 'iter' | 'list' | 'tuple' | 'sorted' | 'set' |
      (any* trailer< '.' 'join' >) )
    trailer< '(' node=any ')' >
    any*
>
"""
p1 = patcomp.compile_pattern(P1)

P2 = """
power<
    'sorted'
    trailer< '(' arglist<node=any any*> ')' >
    any*
>
"""
p2 = patcomp.compile_pattern(P2)

def in_special_context(node):
    patterns = [p0, p1, p2]
    for pattern, parent in zip(patterns, attr_chain(node, "parent")):
        results = {}
        if pattern.match(parent, results) and results["node"] is node:
            return True
    return False
