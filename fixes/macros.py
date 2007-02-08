"""Abstract away often-used node construction routines."""
# Author: Collin Winter

# Python imports
import token

# Local imports
from pytree import Leaf, Node
from pygram import python_symbols as syms


### Constant nodes
ass_leaf = Leaf(token.EQUAL, "=")
ass_leaf.set_prefix(" ")

comma_leaf = Leaf(token.COMMA, ",")
lparen_leaf = Leaf(token.LPAR, "(")
rparen_leaf = Leaf(token.RPAR, ")")

def Assign(target, source):
    """Build an assignment statement"""
    if not isinstance(target, tuple):
        target = (target,)
    if not isinstance(source, tuple):
        source.set_prefix(" ")
        source = (source,)

    return Node(syms.atom, target + (ass_leaf.clone(),) + source)

def Name(name):
    """Return a NAME leaf"""
    return Leaf(token.NAME, name)

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
