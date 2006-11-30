# Copyright 2004-2005 Elemental Security, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

# Modifications:
# Copyright 2006 Python Software Foundation. All Rights Reserved.

"""Syntax tree node definitions.

There is a class or function corresponding to each terminal and
nonterminal symbol.

The grammar is pieced together from the docstrings of the
corresponding classes and functions: text between dollar signs is
assumed to be the right-hand side of the grammar rule corresponding to
that class or function.

We use __slots__ to make the parse tree nodes as small as possible.

NOTE: EVERY CLASS MUST HAVE A __slots__ DEFINITION, EVEN IF EMPTY!
(If not, the instances will get a __dict__, defeating the purpose of
__slots__ in our case.)
"""

__author__ = "Guido van Rossum <guido@python.org>"

# Python imports
import token
import logging

# Pgen imports
from pgen2 import grammar

# Custom logger
logger = logging.getLogger()

class Node(object):
    """Abstract base class for all nodes.

    This has no attributes except a context slot which holds the line
    number (or more detailed context info).  In the future this might
    change this to several slots (e.g. filename, lineno, column, or
    even filename, start_lineno, start_column, end_lineno,
    end_column).  The context is only referenced by two places: the
    part of the code that sticks it in, and the part of the code that
    reports errors.

    In order to reduce the amount of boilerplate code, the context is
    argument is handled by __new__ rather than __init__.  There are
    also a few subclasses that override __new__ to sometimes avoid
    constructing an instance.

    """

    __slots__ = ["context"]

    def __new__(cls, context, *rest):
        assert cls not in (Node, Nonterminal, Terminal, Constant)
        obj = object.__new__(cls)
        obj.context = context
        return obj

    _stretch = False # Set to true to stretch the repr() vertically

    def __repr__(self, repr_arg=repr):
        stretch = self._stretch
        r = [self.__class__.__name__]
        if stretch:
            r.append("(\n    ")
        else:
            r.append("(") # ")" -- crutch for Emacs python-mode :-(
        cls = self.__class__
        # Get nearest non-empty slots __slots__.  This assumes
        # *something* has non-empty __slots__ before we reach object
        # (which has no __slots__).  The class hierarchy guarantees
        # this.
        slots = cls.__slots__
        while not slots:
            cls = cls.__base__
            slots = cls.__slots__
        first = True
        for name in slots:
            if name == "context":
                continue # Skip this
            if first:
                first = False
            else:
                if stretch:
                    r.append(",\n    ")
                else:
                    r.append(", ")
            try:
                value = getattr(self, name)
            except AttributeError:
                continue
            if stretch and isinstance(value, list):
                rr = map(repr_arg, value)
                rv = "[" + ",\n ".join(rr) + "]"
            else:
                rv = repr_arg(value)
            if stretch:
                rv = rv.replace("\n", "\n    ")
            r.append(rv)
        r.append(")")
        return "".join(r)

    def __str__(self):
        return self.__repr__(repr_arg=str)

class Nonterminal(Node):
    """Abstract base class for nonterminal symbols.

    Nothing beyond Node.

    """

    __slots__ = []

    _stretch = True

class Terminal(Node):
    """Abstract base class for terminal symbols.

    Nothing beyond Node.

    """

    __slots__ = []

class Series(Nonterminal):
    """Abstract base class for nonterminals like stmts: stmt+."""

    __slots__ = []

    def __new__(cls, context, *nodes):
        assert cls is not Series
        if len(nodes) == 0:
            return None
        elif len(nodes) == 1:
            return nodes[0]
        else:
            obj = Nonterminal.__new__(cls, context)
            obj.initseries(nodes)
            return obj

class Constant(Terminal):
    """Abstract base class for constants (e.g. number or string).

    Attributes:

    repr -- a string giving the token, exactly as read from source

    """

    __slots__ = ["repr"]

    def __init__(self, context, repr):
        self.repr = repr

    def __str__(self):
        prefix, start = self.context
        return prefix + self.repr

# Node classes for terminal symbols

class Token(Constant):
    """An otherwise unclassified operator or keyword (e.g. '+' or 'if').

    Attributres:

    repr -- a string giving the token's text.

    """

    __slots__ = []

class Name(Terminal):
    """Name (e.g. a variable name or an attribute name).

    Attributes:

    name -- a string giving the name.

    """

    __slots__ = ["name"]

    def __init__(self, context, name):
        self.name = name

    def __str__(self):
        prefix, start = self.context
        return prefix + self.name

class Number(Constant):
    """Numeric constant.

    Nothing beyond Constant.

    """

    __slots__ = []

class String(Constant):
    """String constant.

    Nothing beyond Constant.

    """

    __slots__ = []

# Nodes and factory functions for Python grammar

class VanishingNonterminal(Nonterminal):
    __slots__ = []
    def __new__(cls, context, node):
        return node

class GenericSeries(Series):
    __slots__ = ["nodes"]
    def initseries(self, nodes):
        self.nodes = nodes
    def __str__(self):
        return "".join(map(str, self.nodes))

class atom(GenericSeries):
    __slots__ = []

class power(GenericSeries):
    __slots__ = []

class factor(GenericSeries):
    __slots__ = []

class term(GenericSeries):
    __slots__ = []

class arith_expr(GenericSeries):
    __slots__ = []

class shift_expr(GenericSeries):
    __slots__ = []

class and_expr(GenericSeries):
    __slots__ = []

class xor_expr(GenericSeries):
    __slots__ = []

class or_expr(GenericSeries):
    __slots__ = []

class expr(GenericSeries):
    __slots__ = []

class comparison(GenericSeries):
    __slots__ = []

class not_test(GenericSeries):
    __slots__ = []

class and_test(GenericSeries):
    __slots__ = []

class or_test(GenericSeries):
    __slots__ = []

class test(GenericSeries):
    __slots__ = []

class testlist(GenericSeries):
    __slots__ = []

class expr_stmt(GenericSeries):
    __slots__ = []

class trailer(GenericSeries):
    __slots__ = []

class argument(GenericSeries):
    __slots__ = []

class arglist(GenericSeries):
    __slots__ = []

class subscript(GenericSeries):
    __slots__ = []

class subscriptlist(GenericSeries):
    __slots__ = []

class listmaker(GenericSeries):
    __slots__ = []

class testlist_gexp(GenericSeries):
    __slots__ = []

class suite(GenericSeries):
    __slots__ = []

class if_stmt(GenericSeries):
    __slots__ = []

class compound_stmt(GenericSeries):
    __slots__ = []

class parameters(GenericSeries):
    __slots__ = []

class funcdef(GenericSeries):
    __slots__ = []

class fpdef(GenericSeries):
    __slots__ = []

class varargslist(GenericSeries):
    __slots__ = []

class classdef(GenericSeries):
    __slots__ = []

class exprlist(GenericSeries):
    __slots__ = []

class print_stmt(GenericSeries):
    __slots__ = []

class for_stmt(GenericSeries):
    __slots__ = []

class dotted_name(GenericSeries):
    __slots__ = []

class dotted_as_name(GenericSeries):
    __slots__ = []

class dotted_as_names(GenericSeries):
    __slots__ = []

class import_as_names(GenericSeries):
    __slots__ = []

class import_as_name(GenericSeries):
    __slots__ = []

class import_name(GenericSeries):
    __slots__ = []

class import_from(GenericSeries):
    __slots__ = []

class import_stmt(GenericSeries):
    __slots__ = []

class comp_op(GenericSeries):
    __slots__ = []

class assert_stmt(GenericSeries):
    __slots__ = []

class return_stmt(GenericSeries):
    __slots__ = []

class continue_stmt(GenericSeries):
    __slots__ = []

class break_stmt(GenericSeries):
    __slots__ = []

class flow_stmt(GenericSeries):
    __slots__ = []

class while_stmt(GenericSeries):
    __slots__ = []

class except_clause(GenericSeries):
    __slots__ = []

class try_stmt(GenericSeries):
    __slots__ = []

class dictmaker(GenericSeries):
    __slots__ = []

class raise_stmt(GenericSeries):
    __slots__ = []

class del_stmt(GenericSeries):
    __slots__ = []

class exec_stmt(GenericSeries):
    __slots__ = []

class augassign(GenericSeries):
    __slots__ = []

class global_stmt(GenericSeries):
    __slots__ = []

class fplist(GenericSeries):
    __slots__ = []

class lambdef(GenericSeries):
    __slots__ = []

class old_test(GenericSeries):
    __slots__ = []

class testlist_safe(GenericSeries):
    __slots__ = []

class list_for(GenericSeries):
    __slots__ = []

class decorator(GenericSeries):
    __slots__ = []

class decorators(GenericSeries):
    __slots__ = []

class yield_expr(GenericSeries):
    __slots__ = []

class yield_stmt(GenericSeries):
    __slots__ = []

class list_if(GenericSeries):
    __slots__ = []

class list_iter(GenericSeries):
    __slots__ = []

class gen_for(GenericSeries):
    __slots__ = []

class gen_iter(GenericSeries):
    __slots__ = []

class gen_if(GenericSeries):
    __slots__ = []

class with_var(GenericSeries):
    __slots__ = []

class with_stmt(GenericSeries):
    __slots__ = []

class sliceop(GenericSeries):
    __slots__ = []

class testlist1(GenericSeries):
    __slots__ = []


def _transparent(context, node, *rest):
    assert rest == (), (context, node, rest)
    return node

pass_stmt = _transparent
small_stmt = _transparent
stmt = _transparent

class simple_stmt(GenericSeries):
    __slots__ = []

class file_input(GenericSeries):
    __slots__ = []


# Example nodes and factory functions for nonterminal symbols
# XXX: get rid of these

def Program(context, stmts):
    """Program is a nonterminal with only one non-trivial child.

    Grammar: $ Expression ENDMARKER $

    """
    return stmts

class Expression(Series):
    "Grammar: $ BinaryExpression ['?' BinaryExpression ':' BinaryExpression] $"

    __slots__ = ["test", "left", "right"]

    def initseries(self, nodes):
        self.test, self.left, self.right = nodes

    def __str__(self):
        return "%s ? %s : %s" % (self.test, self.left, self.right)

class BinaryExpression(Series):
    "Grammar: $ Operand (Operator Operand)* $"

    __slots__ = ["left", "op", "right"]

    def initseries(self, stuff):
        # Stuff is a list with alternating operands and operators
        if len(stuff) == 3:
            self.left, self.op, self.right = stuff
            return
        assert len(stuff) > 1 and len(stuff) % 2 == 1
        # Find the rightmost lowest-priority operator
        lowest_i = 1
        lowest_op = stuff[lowest_i]
        lowest_pri = lowest_op.priority()
        for i in range(3, len(stuff), 2):
            op = stuff[i]
            pri = op.priority()
            if pri <= lowest_pri:
                lowest_i = i
                lowest_op = op
                lowest_pri = pri
        self.left = self.__class__(self.context, *stuff[:lowest_i])
        self.op = lowest_op
        self.right = self.__class__(self.context, *stuff[lowest_i+1:])

    def __str__(self):
        return "(%s %s %s)" % (self.left, self.op, self.right)

def Operand(context, arg):
    """Operand is a nonterminal with one child.

    Grammar: $ Atom | UnaryExpression $

    """
    return arg

class UnaryExpression(Nonterminal):
    "Grammar: $ UnaryOperator Operand $"

    __slots__ = ["op", "arg"]

    def __init__(self, context, op, arg):
        self.op = op
        self.arg = arg

    def __str__(self):
        return "%s%s" % (self.op, self.arg)

def UnaryOperator(context, op):
    "Grammar: $ 'not' | '-' $"
    return op

class XXXOperator(Nonterminal):
    """Operator.

    This has a repr slot and a priority() method.

    The __new__ method implements a sort-of singleton pattern: there's
    only one instance per repr value.  (Yes, this means the context is
    not useful.  Therefore we set it to None.)

    Grammar: $ '**' | '*' | '/' | '+' | '-' | '&' | '^' | '|' |
          ['not'] 'in' | '==' | '<' | '>' | '!=' | '<=' | '>=' |
          'and' | 'or' $

    """

    __slots__ = ["repr"]

    _stretch = False

    _cache = {}

    def __new__(cls, context, *args):
        repr = " ".join(args)
        # For "not in", the argument should be the string "not in"
        obj = cls._cache.get(repr)
        if obj is None:
            obj = Terminal.__new__(cls, None)
            obj.repr = repr
        return obj

    def __str__(self):
        return self.repr

    def priority(self):
        return self._priorities[self.repr]

    _priorities = {
        "or":  0,
        "and": 1,
        "in":  2,
        "not in": 2,
        "<":  2,
        ">":  2,
        "==": 2,
        "<=": 2,
        ">=": 2,
        "!=": 2,
        "|":  3,
        "^":  4,
        "&":  5,
        "+":  6,
        "-":  6,
        "*":  7,
        "/":  7,
        "**": 8,
    }

def Atom(context, arg):
    """ Grammar: $ NAME | STRING | NUMBER | ParenthesizedExpression $
    """
    return arg

def ParenthesizedExpression(context, expr):
    "Grammar: $ '(' Expression ')' $"
    return expr


# Conversion from concrete to abstract syntax trees

def vanish(context, value):
    return None

token_mapping = {
    # Tokens that become parse tree nodes
    # (token.NAME is special-cased in the code)
    token.NUMBER: Number,
    token.STRING: String,

##     # Tokens that vanish
##     token.DOT: vanish,
##     token.LPAR: vanish,
##     token.RPAR: vanish,
##     token.COLON: vanish,
##     token.COMMA: vanish,
##     token.EQUAL: vanish,
##     token.DEDENT: vanish,
##     token.INDENT: vanish,
##     token.LBRACE: vanish,
##     token.RBRACE: vanish,
##     token.NEWLINE: vanish,
##     token.ENDMARKER: vanish,
##     grammar.QUESTIONMARK: vanish,

    # All other tokens return the token's string value (e.g. "+")
    }

vanishing_keywords = {
    # E.g. "def": True,
    }

def convert(grammar, node):
    type, value, context, children = node
    # Is it a non-terminal symbol?
    if type in grammar.number2symbol:
        symbol = grammar.number2symbol[type]
        factory = globals().get(symbol)
        if factory is None:
            raise RuntimeError("can't find factory for %s (line %s)" %
                               (symbol, context))
        # Debug variation:
        try:
            return factory(context, *children)
        except:
            logger.debug("%s %s", factory.__name__, "(")
            for child in children:
                logger.debug("%s %s", "==>", child)
            logger.debug(")")
            logger.debug("# Did you remember to declare a 'context' arg?")
            raise
        return factory(context, *children)

    # Must be a terminal symbol.
    if type == token.NAME:
        # Name or keyword.  Special-case the snot out of this.
        if value in grammar.keywords:
            # Keywords become strings, like operators
            if value in vanishing_keywords:
                return None
            else:
                return Token(context, value)
        else:
            return Name(context, value)

    # Look for a handler in the token_mapping table.
    assert type in token.tok_name
    factory = token_mapping.get(type)
    if factory:
        return factory(context, value)
    else:
        return Token(context, value)


# Support code

def generate_grammar(stream):
    """Extract the grammar rules from this module's doc strings."""
    import re
    from types import ModuleType
    lines = []
    startline = None
    for name, obj in globals().items():
        if hasattr(obj, "__doc__") and not isinstance(obj, ModuleType):
            m = re.search(r"Grammar:\s*\$([^$]+)\$", obj.__doc__ or "")
            if m:
                rule = obj.__name__, " ".join(m.group(1).split())
                if rule[0] == "Program":
                    assert not startline
                    startline = rule
                else:
                    lines.append(rule)
    lines.sort()
    # The start symbol *must* be the first rule
    lines.insert(0, startline)
    for name, rhs in lines:
        stream.write("%s: %s\n" % (name, rhs))

if __name__ == '__main__':
    import sys
    generate_grammar(sys.stdout)
