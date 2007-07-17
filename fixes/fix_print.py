# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Fixer for print.

Change:
    'print'          into 'print()'
    'print ...'	     into 'print(...)'
    'print ... ,'    into 'print(..., end=" ")'
    'print >>x, ...' into 'print(..., file=x)'
"""

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.util import Name, Call, Comma, String, is_tuple


class FixPrint(basefix.BaseFix):

    PATTERN = """
              simple_stmt< bare='print' any > | print_stmt
              """

    def transform(self, node, results):
        assert results
        bare_print = results.get("bare")

        if bare_print:
            # Special-case print all by itself
            bare_print.replace(Call(Name("print"), [],
                               prefix=bare_print.get_prefix()))
            return
        assert node.children[0] == Name("print")
        args = node.children[1:]
        sep = end = file = None
        if is_tuple(args[0]):
            # We don't want to keep sticking parens around an
            # already-parenthesised expression.
            return
        if args and args[-1] == Comma():
            args = args[:-1]
            end = " "
        if args and args[0] == pytree.Leaf(token.RIGHTSHIFT, ">>"):
            assert len(args) >= 2
            file = args[1].clone()
            args = args[3:] # Strip a possible comma after the file expression
        # Now synthesize a print(args, sep=..., end=..., file=...) node.
        l_args = [arg.clone() for arg in args]
        if l_args:
            l_args[0].set_prefix("")
        if sep is not None or end is not None or file is not None:
            if sep is not None:
                self.add_kwarg(l_args, "sep", String(repr(sep)))
            if end is not None:
                self.add_kwarg(l_args, "end", String(repr(end)))
            if file is not None:
                self.add_kwarg(l_args, "file", file)
        n_stmt = Call(Name("print"), l_args)
        n_stmt.set_prefix(node.get_prefix())
        return n_stmt

    def add_kwarg(self, l_nodes, s_kwd, n_expr):
        # XXX All this prefix-setting may lose comments (though rarely)
        n_expr.set_prefix("")
        n_argument = pytree.Node(self.syms.argument,
                                 (Name(s_kwd),
                                  pytree.Leaf(token.EQUAL, "="),
                                  n_expr))
        if l_nodes:
            l_nodes.append(Comma())
            n_argument.set_prefix(" ")
        l_nodes.append(n_argument)
