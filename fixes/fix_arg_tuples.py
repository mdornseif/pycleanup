"""Fixer for function definitions with tuple parameters.

def func(((a, b), c), d):
    ...
    
    ->

def func(x, d):
    ((a, b), c) = x
    ...
"""
# Author: Collin Winter

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.macros import Assign, Name, Newline

def is_docstring(stmt):
    return isinstance(stmt, pytree.Node) and \
           stmt.children[0].type == token.STRING

class FixArgTuples(basefix.BaseFix):
    PATTERN = """funcdef< 'def' any parameters< '(' args=any ')' >
                                                ['->' any] ':' suite=any+ >"""

    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        
        new_lines = []
        suite = results["suite"]
        args = results["args"]
        # This crap is so "def foo(...): x = 5; y = 7" is handled correctly.
        if suite[0].children[1].type == token.INDENT:
            start = 2
            indent = suite[0].children[1].value
            end = Newline()
        else:
            start = 0
            indent = "; "
            end = pytree.Leaf(token.INDENT, "")
        
        # We need access to self for new_name(), and making this a method
        #  doesn't feel right. Closing over self and new_lines makes the
        #  code below cleaner.
        def handle_tuple(tuple_arg, add_prefix=False):
            n = Name(self.new_name())
            arg = tuple_arg.clone()
            arg.set_prefix("")
            stmt = Assign(arg, n.clone())
            if add_prefix:
                n.set_prefix(" ")
            tuple_arg.replace(n)
            new_lines.append(pytree.Node(syms.simple_stmt, [stmt, end.clone()]))
        
        if args.type == syms.tfpdef:
            handle_tuple(args)
        elif args.type == syms.typedargslist:
            for i, arg in enumerate(args.children):
                if arg.type == syms.tfpdef:
                    # Without add_prefix, the emitted code is correct,
                    #  just ugly.
                    handle_tuple(arg, add_prefix=(i > 0))
                    
        if not new_lines:
            return node
        
        # This isn't strictly necessary, but it plays nicely with other fixers.
        for line in new_lines:
            line.parent = suite[0]
            
        after = start
        if start == 0:
            new_lines[0].set_prefix(" ")
        elif is_docstring(suite[0].children[start]):
            new_lines[0].set_prefix(indent)
            after = start + 1
            
        children = list(suite[0].children)    
        children[after:after] = new_lines
        for i in range(after+1, after+len(new_lines)+1):
            children[i].set_prefix(indent)
        suite[0].children = tuple(children)
