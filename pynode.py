# Copyright 2004-2005 Elemental Security, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

# Modifications:
# Copyright 2006 Python Software Foundation. All Rights Reserved.

"""Syntax tree node definitions.

There is a class or function corresponding to each terminal and
nonterminal symbol.

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

    # XXX Should refactor this so that there are only two kinds of nodes,
    # Terminal and Nonterminal; each with subclasses to match the grammar
    # or perhaps just storing the node type in a slot.

    """Abstract base class for all nodes.

    This has no attributes except a context slot which holds context
    info (a tuple of the form (prefix, (lineno, column))), and a
    parent slot, which is not set by default but can be set to the
    parent node later.

    In order to reduce the amount of boilerplate code, the context is
    argument is handled by __new__ rather than __init__.  There are
    also a few subclasses that override __new__ to sometimes avoid
    constructing an instance.

    """

    __slots__ = ["context", "parent"]

    def __new__(cls, context, *rest):
        assert cls not in (Node, Nonterminal, Terminal, Constant)
        obj = object.__new__(cls)
        obj.context = context
        return obj

    def get_children(self):
        return ()

    def set_parents(self, parent=None):
        self.parent = parent
        for child in self.get_children():
            child.set_parents(self)

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

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.eq(other)

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is not NotImplemented:
            result = not result
        return result

    def eq(self, other):
        assert self.__class__ is other.__class__
        return self.get_children() == other.get_children()

    def set_prefix(self, new_prefix):
        old_prefix, rest = self.context
        self.context = (new_prefix, rest)

    def get_prefix(self):
        return self.context[0]

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
            obj.init_series(nodes)
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
        prefix, (lineno, column) = self.context
        return prefix + self.repr

    def eq(self, other):
        return self.repr == other.repr

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

    def eq(self, other):
        return self.name == other.name

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

class GenericSeries(Series):

    __slots__ = ["nodes"]

    def init_series(self, nodes):
        self.nodes = nodes

    def get_children(self):
        return self.nodes

    def __str__(self):
        return "".join(map(str, self.nodes))

    def replace(self, old, new):
        self.nodes = tuple((new if n is old else n) for n in self.nodes)

    def set_prefix(self, new_prefix):
        Series.set_prefix(self, new_prefix)
        self.nodes[0].set_prefix(new_prefix)

    def get_prefix(self):
        return self.nodes[0].get_prefix()

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
            # Keywords become Tokens
            return Token(context, value)
        else:
            return Name(context, value)

    assert type in token.tok_name

    # Operators become Tokens
    return Token(context, value)
