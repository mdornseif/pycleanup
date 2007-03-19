"""Fixer for it.next() -> next(it), per PEP 3114."""
# Author: Collin Winter

# Things that currently aren't covered:
#   - listcomp "next" names aren't warned
#   - "with" statement targets aren't checked

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.macros import Name, Call

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
        syms = self.syms
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
            n = Name("__next__")
            n.set_prefix(name.get_prefix())
            name.replace(n)
        elif attr:
            # We don't do this transformation if we're assignment to "x.next".
            # Unfortunately, it doesn't seem possible to do this in PATTERN,
            #  so it's being done here.
            if is_assign_target(syms, node):
                head = results["head"]
                if "".join([str(n) for n in head]).strip() == '__builtin__':
                    self.warning(node, bind_warning)
                return
            attr.replace(Name("__next__"))
        elif "global" in results:
            self.warning(node, bind_warning)
            self.shadowed_next = True
        elif mod:
            n = find_binding(syms, 'next', mod)
            if n:
                self.warning(n, bind_warning)
                self.shadowed_next = True
                
    def finish_tree(self, tree, filename):
        super(FixNext, self).finish_tree(tree, filename)
        if self.shadowed_next:
            for node in self.delayed:
                node.shadowed_next = True


### The following functions are to find module-level bindings

def find_binding(syms, name, file_input):
    for child in file_input.children:
        if child.type == syms.for_stmt:
            if find(name, child.children[1]):
                return child
        elif child.type == syms.funcdef and child.children[1].value == name:
            return child
        elif is_import_binding(syms, child, name):
            return child
        elif child.type == syms.simple_stmt:
            if child.children[0].type == syms.expr_stmt:
                n = find(name, child.children[0].children[0])
                if n:
                    return n

def find(name, node):
    nodes = [node]
    while nodes:
        node = nodes.pop()
        if isinstance(node, pytree.Node):
            nodes.extend(node.children)
        elif node.type == token.NAME and node.value == name:
            return node
    return None

def is_import_binding(syms, node, name):
    if node.type == syms.simple_stmt:
        i = node.children[0]
        if i.type == syms.import_name:
            imp = i.children[1]
            if imp.type == syms.dotted_as_names:
                for child in imp.children:
                    if child.type == syms.dotted_as_name:
                        if child.children[2].value == name:
                            return i
            elif imp.type == syms.dotted_as_name:
                last = imp.children[-1]
                if last.type == token.NAME and last.value == name:
                    return i
        elif i.type == syms.import_from:
            n = i.children[3]
            if n.type == syms.import_as_names:
                if find(name, n):
                    return i
            elif n.type == token.NAME and n.value == name:
                return i
    return None


### The following functions help test if node is part of an assignment
###  target.

try:
    any
except NameError:
    def any(l):
        for o in l:
            if o:
                return True
        return False

def is_assign_target(syms, node):
    assign = find_assign(syms, node)    
    if assign is None:
        return False
            
    for child in assign.children:
        if child.type == token.EQUAL:
            return False
        elif is_subtree(child, node):
            return True
    return False
    
def find_assign(syms, node):
    if node.type == syms.expr_stmt:
        return node
    if node.type == syms.simple_stmt or node.parent is None:
        return None
    return find_assign(syms, node.parent)

def is_subtree(root, node):
    if root == node:
        return True
    return any([is_subtree(c, node) for c in root.children])
