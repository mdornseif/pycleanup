"""Fixer for 'raise E, V, T'"""
# Author: Collin Winter

# Python imports
import token

# Local imports
import pytree
from fixes import basefix
from fixes.macros import Name, Call, Assign, Newline, Attr, is_tuple

class FixRaise(basefix.BaseFix):

    PATTERN = """
    raise_stmt< 'raise' exc=any [',' val=any [',' tb=any]] >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        
        exc = results["exc"].clone()
        if exc.type is token.STRING:
            self.cannot_convert(node, "Python 3 does not support string exceptions")
            return

        # Python 2 supports
        #  raise ((((E1, E2), E3), E4), E5), V
        # as a synonym for
        #  raise E1, V
        # Since Python 3 will not support this, we recurse down any tuple
        # literals, always taking the first element.
        while is_tuple(exc):
            # exc.children[1:-1] is the unparenthesized tuple
            # exc.children[1].children[0] is the first element of the tuple
            exc = exc.children[1].children[0].clone()
        exc.set_prefix(" ")

        if "val" not in results:
            # One-argument raise
            new = pytree.Node(syms.raise_stmt, [Name("raise"), exc])
            new.set_prefix(node.get_prefix())
            return new
        
        val = results["val"].clone()
        if is_tuple(val):
            args = [c.clone() for c in val.children[1:-1]]
        else:
            val.set_prefix("")
            args = [val]

        if "tb" in results:
            tb = results["tb"].clone()
            name = Name(self.new_name())
            children = list(node.parent.parent.children)
            i = children.index(node.parent)
            indent = children[1].value

            # Instance the exception
            build_e = pytree.Node(syms.simple_stmt,
                                  [Assign(name.clone(), Call(exc, args)),
                                   Newline()])
            build_e.parent = node.parent.parent
            if node.get_prefix():
                # Over-indents otherwise
                build_e.set_prefix(indent)

            # Assign the traceback
            set_tb = pytree.Node(syms.simple_stmt,
                                 [Assign(Attr(name.clone(), Name("__traceback__")), tb),
                                  Newline()])
            set_tb.set_prefix(indent)
            set_tb.parent = node.parent.parent

            # Insert into the suite
            children[i:i] = [build_e, set_tb]
            node.parent.parent.children = tuple(children)

            name.set_prefix(" ")
            new = pytree.Node(syms.simple_stmt, [Name("raise"), name])
            new.set_prefix(indent)
            return new
        else:
            new = pytree.Node(syms.raise_stmt, [Name("raise"), Call(exc, args)])
            new.set_prefix(node.get_prefix())
            return new
