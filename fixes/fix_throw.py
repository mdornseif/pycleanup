"""Fixer for generator.throw(E, V, T).

g.throw(E)       -> g.throw(E)
g.throw(E, V)    -> g.throw(E(V))
g.throw(E, V, T) -> g.throw(E(V).with_traceback(T))

g.throw("foo"[, V[, T]]) will warn about string exceptions."""
# Author: Collin Winter

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.util import Name, Call, ArgList, Attr, is_tuple

class FixThrow(basefix.BaseFix):

    PATTERN = """
    power< any trailer< '.' 'throw' >
           trailer< '(' args=arglist< exc=any ',' val=any [',' tb=any] > ')' >
    >
    |
    power< any trailer< '.' 'throw' > trailer< '(' exc=any ')' > >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results

        exc = results["exc"].clone()
        if exc.type is token.STRING:
            self.cannot_convert(node, "Python 3 does not support string exceptions")
            return
            
        # Leave "g.throw(E)" alone
        val = results.get("val")
        if val is None:
            return 

        val = val.clone()
        if is_tuple(val):
            args = [c.clone() for c in val.children[1:-1]]
        else:
            val.set_prefix("")
            args = [val]

        throw_args = results["args"]

        if "tb" in results:
            tb = results["tb"].clone()
            tb.set_prefix("")
            
            e = Call(exc, args)
            with_tb = Attr(e, Name('with_traceback'))
            call_wtb = list(with_tb + (ArgList([tb]),))
            
            throw_args.replace(pytree.Node(syms.power, call_wtb))
            # No return
        else:
            throw_args.replace(Call(exc, args))
            # No return
