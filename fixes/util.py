"""Utility functions, node construction macros, etc."""
# Author: Collin Winter

# Local imports
from pgen2 import token
from pytree import Leaf, Node
from pygram import python_symbols as syms


###########################################################
### Common node-construction "macros"
###########################################################

def KeywordArg(keyword, value):
    return Node(syms.argument,
                [keyword, Leaf(token.EQUAL, '='), value])

def LParen():
    return Leaf(token.LPAR, "(")

def RParen():
    return Leaf(token.RPAR, ")")

def Assign(target, source):
    """Build an assignment statement"""
    if not isinstance(target, list):
        target = [target]
    if not isinstance(source, list):
        source.set_prefix(" ")
        source = [source]

    return Node(syms.atom,
                target + [Leaf(token.EQUAL, "=", prefix=" ")] + source)

def Name(name, prefix=None):
    """Return a NAME leaf"""
    return Leaf(token.NAME, name, prefix=prefix)

def Attr(obj, attr):
    """A node tuple for obj.attr"""
    return [obj, Node(syms.trailer, [Dot(), attr])]

def Comma():
    """A comma leaf"""
    return Leaf(token.COMMA, ",")

def Dot():
    """A period (.) leaf"""
    return Leaf(token.DOT, ".")

def ArgList(args, lparen=LParen(), rparen=RParen()):
    """A parenthesised argument list, used by Call()"""
    return Node(syms.trailer,
                [lparen.clone(),
                 Node(syms.arglist, args),
                 rparen.clone()])

def Call(func_name, args, prefix=None):
    """A function call"""
    node = Node(syms.power, [func_name, ArgList(args)])
    if prefix is not None:
        node.set_prefix(prefix)
    return node

def Newline():
    """A newline literal"""
    return Leaf(token.NEWLINE, "\n")

def Number(n, prefix=None):
    return Leaf(token.NUMBER, n, prefix=prefix)

def Subscript(index_node):
    """A numeric or string subscript"""
    return Node(syms.trailer, [Leaf(token.LBRACE, '['),
                               index_node,
                               Leaf(token.RBRACE, ']')])

def String(string, prefix=None):
    """A string leaf"""
    return Leaf(token.STRING, string, prefix=prefix)

def ListComp(xp, fp, it, test=None):
    """A list comprehension of the form [xp for fp in it if test].

    If test is None, the "if test" part is omitted.
    """
    xp.set_prefix("")
    fp.set_prefix(" ")
    it.set_prefix(" ")
    for_leaf = Leaf(token.NAME, "for")
    for_leaf.set_prefix(" ")
    in_leaf = Leaf(token.NAME, "in")
    in_leaf.set_prefix(" ")
    inner_args = [for_leaf, fp, in_leaf, it]
    if test:
        test.set_prefix(" ")
        if_leaf = Leaf(token.NAME, "if")
        if_leaf.set_prefix(" ")
        inner_args.append(Node(syms.comp_if, [if_leaf, test]))
    inner = Node(syms.listmaker, [xp, Node(syms.comp_for, inner_args)])
    return Node(syms.atom,
                       [Leaf(token.LBRACE, "["),
                        inner,
                        Leaf(token.RBRACE, "]")])

###########################################################
### Determine whether a node represents a given literal
###########################################################

def is_tuple(node):
    """Does the node represent a tuple literal?"""
    if isinstance(node, Node) and node.children == [LParen(), RParen()]:
        return True
    return (isinstance(node, Node)
            and len(node.children) == 3
            and isinstance(node.children[0], Leaf)
            and isinstance(node.children[1], Node)
            and isinstance(node.children[2], Leaf)
            and node.children[0].value == "("
            and node.children[2].value == ")")

def is_list(node):
    """Does the node represent a list literal?"""
    return (isinstance(node, Node)
            and len(node.children) > 1
            and isinstance(node.children[0], Leaf)
            and isinstance(node.children[-1], Leaf)
            and node.children[0].value == "["
            and node.children[-1].value == "]")

###########################################################
### Common portability code. This allows fixers to do, eg,
###  "from fixes.util import set" and forget about it.
###########################################################

try:
    any = any
except NameError:
    def any(l):
        for o in l:
            if o:
                return True
        return False

try:
    set = set
except NameError:
    from sets import Set as set

try:
    reversed = reversed
except NameError:
    def reversed(l):
        return l[::-1]

###########################################################
### Misc
###########################################################

def attr_chain(obj, attr):
    """Follow an attribute chain.
    
    If you have a chain of objects where a.foo -> b, b.foo-> c, etc,
    use this to iterate over all objects in the chain. Iteration is
    terminated by getattr(x, attr) is None.
    
    Args:
        obj: the starting object
        attr: the name of the chaining attribute
    
    Yields:
        Each successive object in the chain.
    """
    next = getattr(obj, attr)
    while next:
        yield next
        next = getattr(next, attr)

###########################################################
### The following functions are to find bindings in a suite
###########################################################

def make_suite(node):
    if node.type == syms.suite:
        return node
    node = node.clone()
    parent, node.parent = node.parent, None
    suite = Node(syms.suite, [node])
    suite.parent = parent
    return suite

_def_syms = set([syms.classdef, syms.funcdef])
def find_binding(name, node):
    for child in node.children:
        if child.type == syms.for_stmt:
            if _find(name, child.children[1]):
                return child
            n = find_binding(name, make_suite(child.children[-1]))
            if n:
                return n
        elif child.type in (syms.if_stmt, syms.while_stmt):
            n = find_binding(name, make_suite(child.children[-1]))
            if n:
                return n
        elif child.type == syms.try_stmt:
            n = find_binding(name, make_suite(child.children[2]))
            if n:
                return n
            for i, kid in enumerate(child.children[3:]):
                if kid.type == token.COLON and kid.value == ":":
                    # i+3 is the colon, i+4 is the suite
                    n = find_binding(name, make_suite(child.children[i+4]))
                    if n:
                        return n
        elif child.type in _def_syms and child.children[1].value == name:
            return child
        elif _is_import_binding(child, name):
            return child
        elif child.type == syms.simple_stmt:
            if child.children[0].type == syms.expr_stmt:
                if _find(name, child.children[0].children[0]):
                    return child.children[0]

_block_syms = set([syms.funcdef, syms.classdef, syms.trailer])
def _find(name, node):
    nodes = [node]
    while nodes:
        node = nodes.pop()
        if node.type > 256 and node.type not in _block_syms:
            nodes.extend(node.children)
        elif node.type == token.NAME and node.value == name:
            return node
    return None

def _is_import_binding(node, name):
    if node.type == syms.simple_stmt:
        i = node.children[0]
        if i.type == syms.import_name:
            imp = i.children[1]
            if imp.type == syms.dotted_as_names:
                for child in imp.children:
                    if child.type == syms.dotted_as_name:
                        if child.children[2].value == name:
                            return i
                    elif child.type == token.NAME and child.value == name:
                        return i
            elif imp.type == syms.dotted_as_name:
                last = imp.children[-1]
                if last.type == token.NAME and last.value == name:
                    return i
            elif imp.type == token.NAME and imp.value == name:
                return i
        elif i.type == syms.import_from:
            n = i.children[3]
            if n.type == syms.import_as_names and _find(name, n):
                return i
            elif n.type == syms.import_as_name:
                child = n.children[2]
                if child.type == token.NAME and child.value == name:
                    return i
            elif n.type == token.NAME and n.value == name:
                return i
    return None
