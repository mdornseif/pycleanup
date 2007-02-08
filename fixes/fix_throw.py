"""Fixer for generator.throw(E, V, T)"""
# Author: Collin Winter

# Python imports
import token

# Local imports
import pytree
from fixes import basefix
from fixes.macros import Name, Call, Assign, Newline, Attr

class FixThrow(basefix.BaseFix):

    PATTERN = """
    power< any trailer< '.' 'throw' >
           trailer< '(' args=arglist< exc=any ',' val=any [',' tb=any] > ')' >
         >
    """

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results

        throw_args = results["args"]
        exc = results["exc"].clone()
        args = [results["val"].clone()]
        args[0].set_prefix("")

        if "tb" in results:
            tb = results["tb"].clone()
            name = Name(self.new_name())
            suite = find_parent_suite(node)
            stmts = list(suite.children)
            node_stmt = find_stmt(stmts, node)
            i = stmts.index(node_stmt)
            indent = stmts[1].value

            # Instance the exception
            build_e = pytree.Node(syms.simple_stmt,
                                  [Assign(name.clone(), Call(exc, args)),
                                   Newline()])
            build_e.parent = node.parent.parent
            if node_stmt.get_prefix():
                # Over-indents otherwise
                build_e.set_prefix(indent)

            # Assign the traceback
            tb.set_prefix(" ")
            set_tb = pytree.Node(syms.simple_stmt,
                                 [Assign(Attr(name.clone(),
                                              Name("__traceback__")), tb),
                                  Newline()])
            set_tb.set_prefix(indent)
            set_tb.parent = node.parent.parent

            # Insert into the suite
            stmts[i:i] = [build_e, set_tb]
            suite.children = tuple(stmts)

            throw_args.replace(name)
            if not node_stmt.get_prefix():
                node_stmt.set_prefix(indent)
            # No return
        else:
            throw_args.replace(Call(exc, args))
            # No return


def find_parent_suite(node):
    parent = node.parent
    while parent:
        if len(parent.children) > 2 and parent.children[0].value == "\n":
            return parent
        parent = parent.parent

def find_stmt(stmts, node):
    while node not in stmts:
        node = node.parent
    return node
