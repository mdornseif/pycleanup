# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Python parse tree definitions.

This is a very concrete parse tree; we need to keep every token and
even the comments and whitespace between tokens.

There's also a matching pattern implementation here.
"""

__author__ = "Guido van Rossum <guido@python.org>"


class Base(object):

    """Abstract base class for Node and Leaf.

    This provides some default functionality and boilerplate using the
    template pattern.

    A node may be a subnode of at most one parent.
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
        # If there's exactly one child, return that child instead of
        # creating a new node.
        if len(children) == 1:
            return children[0]
        return Node(type, children, context=context)
    else:
        return Leaf(type, value, context=context)


class BasePattern(object):

    """A pattern is a tree matching pattern.

    It looks for a specific node type (token or symbol), and
    optionally for a specific content.
    """

    # Defaults for instance variables
    type = None     # Node type (token if < 256, symbol if >= 256)
    content = None  # Optional content matching pattern
    name = None     # Optional name used to store match in results dict

    def __new__(cls, *args, **kwds):
        """Constructor that prevents BasePattern from being instantiated."""
        assert cls is not BasePattern, "Cannot instantiate BasePattern"
        return object.__new__(cls, *args, **kwds)

    def match(self, node, results=None):
        """Does that node match this pattern?

        Returns True if it matches, False if not.

        If results is not None, it must be a dict which will be
        updated with the nodes matching named subpatterns.
        """
        if self.type is not None and node.type != self.type:
            return False
        if self.content is not None:
            r = None
            if results is not None:
                r = {}
            if not self._submatch(node, r):
                return False
            if r:
                results.update(r)
        if results is not None and self.name is not None:
            results[self.name] = node
        return True


class NodePattern(BasePattern):

    def __init__(self, type=None, content=None, name=None):
        """Constructor.  Takes optional type, content, and name.

        The type, if given, must be a symbol type (>= 256).

        The content, if given, must be a sequence of Patterns that
        must match the node's children exactly.

        If a name is given, the matching node is stored in the results
        dict under that key.
        """
        if type is not None:
            assert type >= 256, type
        else:
            assert content is None, repr(content)
        if content is not None:
            assert not isinstance(content, basestring), repr(content)
            content = tuple(content)
            for i, item in enumerate(content):
                assert isinstance(item, BasePattern), (i, item)
        self.type = type
        self.content = content
        self.name = name

    def _submatch(self, node, results=None):
        """Match the pattern's content to the node's children.

        This assumes the node type matches and self.content is not None.

        Returns True if it matches, False if not.

        If results is not None, it must be a dict which will be
        updated with the nodes matching named subpatterns.

        When returning False, the results dict may still be updated.
        """
        if len(self.content) != len(node.children):
            return False
        for subpattern, child in zip(self.content, node.children):
            if not subpattern.match(child, results):
                return False
        return True


class LeafPattern(BasePattern):

    def __init__(self, type, content=None, name=None):
        """Constructor.  Takes a type, optional content, and optional name.

        The type must be a token type (< 256).

        The content, if given, must be a string.

        If a name is given, the matching node is stored in the results
        dict under that key.
        """
        assert type < 256, type
        if content is not None:
            assert isinstance(content, basestring), repr(content)
        self.type = type
        self.content = content
        self.name = name

    def _submatch(self, node, results=None):
        """Match the pattern's content to the node's children.

        This assumes the node type matches and self.content is not None.

        Returns True if it matches, False if not.

        If results is not None, it must be a dict which will be
        updated with the nodes matching named subpatterns.

        When returning False, the results dict may still be updated.
        """
        return self.content == node.value
