# Copyright 2006 Georg Brandl.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for intern().

intern(s) -> sys.intern(s)"""

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.util import Name, Attr


class FixIntern(basefix.BaseFix):

    PATTERN = """
    power< 'intern'
           trailer< lpar='('
                    ( not(arglist | argument<any '=' any>) obj=any
                      | obj=arglist<(not argument<any '=' any>) any ','> )
                    rpar=')' >
           after=any*
    >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        obj = results["obj"].clone()
        if obj.type == syms.arglist:
            newarglist = obj.clone()
        else:
            newarglist = pytree.Node(syms.arglist, [obj.clone()])
        after = results["after"]
        if after:
            after = tuple([n.clone() for n in after])
        new = pytree.Node(syms.power,
                          Attr(Name("sys"), Name("intern")) +
                          (pytree.Node(syms.trailer,
                                       [results["lpar"].clone(),
                                        newarglist,
                                        results["rpar"].clone()]),)
                          + after)
        new.set_prefix(node.get_prefix())
        return new
