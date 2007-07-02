# Copyright 2007 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer that changes filter(F, X) into list(filter(F, X)).

We avoid the transformation if the filter() call is directly contained
in iter(<>), list(<>), tuple(<>), sorted(<>), ...join(<>), or
for V in <>:.

NOTE: This is still not correct if the original code was depending on
filter(F, X) to return a string if X is a string and a tuple if X is a
tuple.  That would require type inference, which we don't do.  Let
Python 2.6 figure it out.
"""

# Local imports
import pytree
import patcomp
from pgen2 import token
from fixes import basefix
from fixes.util import Name, Call, ListComp

class FixFilter(basefix.BaseFix):

    PATTERN = """
    filter_lambda=power<
        'filter'
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
        'filter'
        args=trailer< '(' [any] ')' >
    >
    """

    def transform(self, node):
        results = self.match(node)
        if "filter_lambda" in results:
            new = ListComp(results.get("fp").clone(),
                           results.get("fp").clone(),
                           results.get("it").clone(),
                           results.get("xp").clone())
        else:
            if self.in_special_context(node):
                return None
            new = node.clone()
            new.set_prefix("")
            new = Call(Name("list"), [new])
        new.set_prefix(node.get_prefix())
        return new

    P0 = """for_stmt< 'for' any 'in' node=any ':' any* >
            | list_for< 'for' any 'in' node=any any* >
            | gen_for< 'for' any 'in' node=any any* >
         """
    p0 = patcomp.PatternCompiler().compile_pattern(P0)

    P1 = """
    power<
        NAME< 'iter' | 'list' | 'tuple' | 'sorted' >
        trailer< '(' node=any ')' >
        any*
    >
    """
    p1 = patcomp.PatternCompiler().compile_pattern(P1)

    P2 = """
    power<
        'sorted'
        trailer< '(' arglist<node=any any*> ')' >
        any*
    >
    """
    p2 = patcomp.PatternCompiler().compile_pattern(P2)

    def in_special_context(self, node):
        p = node.parent
        if p is None:
            return False
        results = {}
        if self.p0.match(p, results) and results["node"] is node:
            return True

        pp = p.parent
        if pp is None:
            return False
        results = {}
        if self.p1.match(pp, results) and results["node"] is node:
            return True

        ppp = pp.parent
        if ppp is None:
            return False
        results = {}
        if self.p2.match(ppp, results) and results["node"] is node:
            return True
        
        return False
