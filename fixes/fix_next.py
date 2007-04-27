"""Fixer for it.next() -> next(it), per PEP 3114."""
# Author: Collin Winter

# Things that currently aren't covered:
#   - listcomp "next" names aren't warned
#   - "with" statement targets aren't checked

# Local imports
import pytree
from pgen2 import token
from pygram import python_symbols as syms
from fixes import basefix
from fixes.util import Name, Call, find_binding, any

bind_warning = "Calls to builtin next() possibly shadowed by global binding"


class DelayedStrNode(object):

    def __init__(self, type, base):
        self.parent = None
        self.shadowed_next = False
        self.base = base
        self.type = type
        self.value = ""

    def __str__(self):
        b = "".join([str(n) for n in self.base])
        if self.shadowed_next:
            return "%s.__next__()" % b
        else:
            return "next(%s)" % b

    def clone(self):
        node = DelayedStrNode(self.type, self.base)
        node.shadowed_next = self.shadowed_next
        node.value = self.value
        return node


class FixNext(basefix.BaseFix):
    PATTERN = """
    power< base=any+ trailer< '.' 'next' > trailer< '(' ')' > >
    |
    power< head=any+ trailer< '.' attr='next' > not trailer< '(' ')' > >
    |
    classdef< 'class' any+ ':'
              suite< any*
                     funcdef< 'def'
                              name='next'
                              parameters< '(' NAME ')' > any+ >
                     any* > >
    |
    global=global_stmt< 'global' any* 'next' any* >
    |
    mod=file_input< any+ >
    """
    
    def start_tree(self, tree, filename):
        super(FixNext, self).start_tree(tree, filename)
        self.shadowed_next = False
        self.delayed = []
    
    def transform(self, node):
        results = self.match(node)
        assert results
        
        base = results.get("base")
        attr = results.get("attr")
        name = results.get("name")
        mod = results.get("mod")
        
        if base:
            n = DelayedStrNode(syms.power, base)
            node.replace(n)
            self.delayed.append(n)
        elif name:
            n = Name("__next__", prefix=name.get_prefix())
            name.replace(n)
        elif attr:
            # We don't do this transformation if we're assigning to "x.next".
            # Unfortunately, it doesn't seem possible to do this in PATTERN,
            #  so it's being done here.
            if is_assign_target(node):
                head = results["head"]
                if "".join([str(n) for n in head]).strip() == '__builtin__':
                    self.warning(node, bind_warning)
                return
            attr.replace(Name("__next__"))
        elif "global" in results:
            self.warning(node, bind_warning)
            self.shadowed_next = True
        elif mod:
            n = find_binding('next', mod)
            if n:
                self.warning(n, bind_warning)
                self.shadowed_next = True
                
    def finish_tree(self, tree, filename):
        super(FixNext, self).finish_tree(tree, filename)
        if self.shadowed_next:
            for node in self.delayed:
                node.shadowed_next = True


### The following functions help test if node is part of an assignment
###  target.

def is_assign_target(node):
    assign = find_assign(node)    
    if assign is None:
        return False
            
    for child in assign.children:
        if child.type == token.EQUAL:
            return False
        elif is_subtree(child, node):
            return True
    return False
    
def find_assign(node):
    if node.type == syms.expr_stmt:
        return node
    if node.type == syms.simple_stmt or node.parent is None:
        return None
    return find_assign(node.parent)

def is_subtree(root, node):
    if root == node:
        return True
    return any([is_subtree(c, node) for c in root.children])
