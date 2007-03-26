"""Utility functions, node construction macros, etc."""
# Author: Collin Winter

# Local imports
from pgen2 import token
from pytree import Leaf, Node
from pygram import python_symbols as syms


### Constant nodes
ass_leaf = Leaf(token.EQUAL, "=")
ass_leaf.set_prefix(" ")

comma_leaf = Leaf(token.COMMA, ",")
lparen_leaf = Leaf(token.LPAR, "(")
rparen_leaf = Leaf(token.RPAR, ")")

###########################################################
### Common node-construction "macros"
###########################################################

def Assign(target, source):
    """Build an assignment statement"""
    if not isinstance(target, tuple):
        target = (target,)
    if not isinstance(source, tuple):
        source.set_prefix(" ")
        source = (source,)

    return Node(syms.atom, target + (ass_leaf.clone(),) + source)

def Name(name, prefix=None):
    """Return a NAME leaf"""
    return Leaf(token.NAME, name, prefix=prefix)

def Attr(obj, attr):
    """A node tuple for obj.attr"""
    return (obj,
            Node(syms.trailer, [Leaf(token.DOT, '.'),
                                attr]))

def Comma():
    """A comma leaf"""
    return comma_leaf.clone()

def ArgList(args, lparen=lparen_leaf, rparen=rparen_leaf):
    """A parenthesised argument list, used by Call()"""
    return Node(syms.trailer,
                [lparen.clone(),
                 Node(syms.arglist, args),
                 rparen.clone()])

def Call(func_name, args):
    """A function call"""
    return Node(syms.power, [func_name, ArgList(args)])

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
    
###########################################################
### Determine whether a node represents a given literal
###########################################################

def is_tuple(node):
    """Does the node represent a tuple literal?"""
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
