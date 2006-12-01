# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Python parse tree definitions.

This is a very concrete parse tree; we need to keep every token and
even the comments and whitespace between tokens.

A node may be a subnode of at most one parent.
"""

__author__ = "Guido van Rossum <guido@python.org>"


class Base(object):

    """Abstract base class for Node and Leaf.

    This provides some default functionality and boilerplate using the
    template pattern.
    """

    # Default values for instance variables
    type = None    # int: token number (< 256) or symbol number (>= 256)
    parent = None  # Parent node pointer, or None
    children = ()  # Tuple of subnodes

    def __new__(cls, *args, **kwds):
        """Constructor that prevents Base from being instantiated."""
        assert cls is not Base, "Cannot instantiate Base"
        return object.__new__(cls, *args, **kwds)

    def __eq__(self, other):
        """Compares two nodes for equality.

        This calls the method _eq().
        """
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self._eq(other)

    def __ne__(self, other):
        """Compares two nodes for inequality.

        This calls the method _eq().
        """
        if self.__class__ is not other.__class__:
            return NotImplemented
        return not self._eq(other)

    def _eq(self, other):
        """Compares two nodes for equality.

        This is called by __eq__ and __ne__.  It is only called if the
        two nodes have the same type.  This must be implemented by the
        concrete subclass.  Nodes should be considered equal if they
        have the same structure, ignoring the prefix string and other
        context information.
        """
        raise NotImplementedError

    def set_prefix(self, prefix):
        """Sets the prefix for the node (see Leaf class).

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError

    def get_prefix(self):
        """Returns the prefix for the node (see Leaf class).

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError


class Node(Base):

    """Concrete implementation for interior nodes."""

    def __init__(self, type, children, context=None):
        """Initializer.

        Takes a type constant (a symbol number >= 256), a sequence of
        child nodes, and an optional context keyword argument.

        As a side effect, the parent pointers of the children are updated.
        """
        assert type >= 256, type
        self.type = type
        self.children = tuple(children)
        for ch in self.children:
            ch.parent = self

    def __repr__(self):
        """Returns a canonical string representation."""
        return "%s(%r, %r)" % (self.__class__.__name__,
                               self.type,
                               self.children)

    def __str__(self):
        """Returns a pretty string representation.

        This reproduces the input source exactly.
        """
        return "".join(map(str, self.children))

    def _eq(self, other):
        """Compares two nodes for equality."""
        return (self.type, self.children) == (other.type, other.children)

    def set_prefix(self, prefix):
        """Sets the prefix for the node.

        This passes the responsibility on to the first child.
        """
        if self.children:
            self.children[0].set_prefix(prefix)

    def get_prefix(self):
        """Returns the prefix for the node.

        This passes the call on to the first child.
        """
        if not self.children:
            return ""
        return self.children[0].get_prefix()

    def replace(self, new):
        """Replaces this node with a new one in the parent.

        This can also be used to remove this node from the parent by
        passing None.
        """
        assert self.parent is not None, str(self)
        assert new is None or new.parent is None, str(new)
        l_children = []
        found = False
        for ch in self.parent.children:
            if ch is self:
                assert not found, (self.parent.children, self, new)
                if new is not None:
                    l_children.append(new)
                found = True
            else:
                l_children.append(ch)
        assert found, (self.children, self, new)
        self.parent.children = tuple(l_children)
        if new is not None:
            new.parent = self.parent
        self.parent = None


class Leaf(Base):

    """Concrete implementation for leaf nodes."""

    # Default values for instance variables
    prefix = ""  # Whitespace and comments preceding this token in the input
    lineno = 0   # Line where this token starts in the input
    column = 0   # Column where this token tarts in the input

    def __init__(self, type, value, context=None):
        """Initializer.

        Takes a type constant (a token number < 256), a string value,
        and an optional context keyword argument.
        """
        assert 0 <= type < 256, type
        if context is not None:
            self.prefix, (self.lineno, self.column) = context
        self.type = type
        self.value = value

    def __repr__(self):
        """Returns a canonical string representation."""
        return "%s(%r, %r)" % (self.__class__.__name__,
                               self.type,
                               self.value)

    def __str__(self):
        """Returns a pretty string representation.

        This reproduces the input source exactly.
        """
        return self.prefix + self.value

    def _eq(self, other):
        """Compares two nodes for equality."""
        return (self.type, self.value) == (other.type, other.value)

    def set_prefix(self, prefix):
        """Sets the prefix for the node."""
        self.prefix = prefix

    def get_prefix(self):
        """Returns the prefix for the node."""
        return self.prefix


def convert(gr, raw_node):
    """Converts raw node information to a Node or Leaf instance.

    This is passed to the parser driver which calls it whenever a
    reduction of a grammar rule produces a new complete node, so that
    the tree is build strictly bottom-up.
    """
    type, value, context, children = raw_node
    if children or type in gr.number2symbol:
        # XXX If there's exactly one child, should return that child
        # instead of synthesizing a new node.
        return Node(type, children, context=context)
    else:
        return Leaf(type, value, context=context)
