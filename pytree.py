# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Python parse tree definitions.

This is a very concrete parse tree; we need to keep every token and
even the comments and whitespace between tokens.

There's also a pattern matching implementation here.
"""

__author__ = "Guido van Rossum <guido@python.org>"

import sys


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
            assert ch.parent is None, str(ch)
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

    This is an abstract base class.  There are three concrete
    subclasses:

    - LeafPattern matches a single leaf node;
    - NodePattern matches a single node (usually non-leaf);
    - WildcardPattern matches a sequence of nodes of variable length.
    """

    # Defaults for instance variables
    type = None     # Node type (token if < 256, symbol if >= 256)
    content = None  # Optional content matching pattern
    name = None     # Optional name used to store match in results dict

    def __new__(cls, *args, **kwds):
        """Constructor that prevents BasePattern from being instantiated."""
        assert cls is not BasePattern, "Cannot instantiate BasePattern"
        return object.__new__(cls, *args, **kwds)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join("%s=%r" % (x, getattr(self, x))
                                     for x in ("type", "content", "name")
                                     if getattr(self, x) is not None))

    def match(self, node, results=None):
        """Does this pattern exactly match a node?

        Returns True if it matches, False if not.

        If results is not None, it must be a dict which will be
        updated with the nodes matching named subpatterns.

        Default implementation for non-wildcard patterns.
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
        if results is not None and self.name:
            results[self.name] = node
        return True

    def match_seq(self, nodes, results=None):
        """Does this pattern exactly match a sequence of nodes?

        Default implementation for non-wildcard patterns.
        """
        if len(nodes) != 1:
            return False
        return self.match(nodes[0], results)

    def generate_matches(self, nodes):
        """Generator yielding all matches for this pattern.

        Default implementation for non-wildcard patterns.
        """
        r = {}
        if nodes and self.match(nodes[0], r):
            yield 1, r


class LeafPattern(BasePattern):

    def __init__(self, type=None, content=None, name=None):
        """Initializer.  Takes optional type, content, and name.

        The type, if given must be a token type (< 256).  If not given,
        this matches any *leaf* node; the content may still be required.

        The content, if given, must be a string.

        If a name is given, the matching node is stored in the results
        dict under that key.
        """
        if type is not None:
            assert 0 <= type < 256, type
        if content is not None:
            assert isinstance(content, basestring), repr(content)
        self.type = type
        self.content = content
        self.name = name

    def match(self, node, results=None):
        """Override match() to insist on a leaf node."""
        if not isinstance(node, Leaf):
            return False
        return BasePattern.match(self, node, results)

    def _submatch(self, node, results=None):
        """Match the pattern's content to the node's children.

        This assumes the node type matches and self.content is not None.

        Returns True if it matches, False if not.

        If results is not None, it must be a dict which will be
        updated with the nodes matching named subpatterns.

        When returning False, the results dict may still be updated.
        """
        return self.content == node.value


class NodePattern(BasePattern):

    wildcards = False

    def __init__(self, type=None, content=None, name=None):
        """Initializer.  Takes optional type, content, and name.

        The type, if given, must be a symbol type (>= 256).  If the
        type is None, the content must be None, and this matches *any*
        single node (leaf or not).

        The content, if not None, must be a sequence of Patterns that
        must match the node's children exactly.  If the content is
        given, the type must not be None.

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
                if isinstance(item, WildcardPattern):
                    self.wildcards = True
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
        if self.wildcards:
            for c, r in generate_matches(self.content, node.children):
                if c == len(node.children):
                    if results is not None:
                        results.update(r)
                    return True
            return False
        if len(self.content) != len(node.children):
            return False
        for subpattern, child in zip(self.content, node.children):
            if not subpattern.match(child, results):
                return False
        return True


class WildcardPattern(BasePattern):

    """A wildcard pattern can match zero or more nodes."""

    def __init__(self, content=None, min=0, max=sys.maxint, name=None):
        """Initializer.

        Args:
            content: optional sequence of subsequences of patterns;
                     if absent, matches one node;
                     if present, each subsequence is an alternative [*]
            min: optinal minumum number of times to match, default 0
            max: optional maximum number of times tro match, default sys.maxint
            name: optional name assigned to this match

        [*] Thus, if content is [[a, b, c], [d, e], [f, g, h]] this is
            equivalent to (a b c | d e | f g h); if content is None,
            this is equivalent to '.' in regular expression terms.
            The min and max parameters work as follows:
                min=0, max=maxint: .*
                min=1, max=maxint: .+
                min=0, max=1: .?
                min=1, max=1: .
            If content is not None, replace the dot with the parenthesized
            list of alternatives, e.g. (a b c | d e | f g h)*
        """
        assert 0 <= min <= max <= sys.maxint, (min, max)
        if content is not None:
            content = tuple(map(tuple, content))  # Protect against alterations
            # Check sanity of alternatives
            assert len(content), repr(content)  # Can't have zero alternatives
            for alt in content:
                assert len(alt), repr(alt) # Can have empty alternatives
        self.content = content
        self.min = min
        self.max = max
        self.name = name

    def match(self, node, results=None):
        """Does this pattern exactly match a node?"""
        return self.match_seq([node], results)

    def match_seq(self, nodes, results=None):
        """Does this pattern exactly match a sequence of nodes?"""
        for c, r in self.generate_matches(nodes):
            if c == len(nodes):
                if results is not None:
                    results.update(r)
                    if self.name:
                        results[self.name] = tuple(nodes)
                return True
        return False

    def generate_matches(self, nodes):
        """Generator yielding matches for a sequence of nodes.

        Args:
            nodes: sequence of nodes

        Yields:
            (count, results) tuples where:
            count: the match comprises nodes[:count];
            results: dict containing named submatches.
        """
        if self.content is None:
            # Shortcut for special case (see __init__.__doc__)
            for count in xrange(self.min, 1 + min(len(nodes), self.max)):
                r = {}
                if self.name:
                    r[self.name] = nodes[:count]
                yield count, r
        else:
            for count, r in self._recursive_matches(nodes, 0):
                if self.name:
                    r[self.name] = nodes[:count]
                yield count, r

    def _recursive_matches(self, nodes, count):
        """Helper to recursively yield the matches."""
        assert self.content is not None
        if count >= self.min:
            r = {}
            if self.name:
                r[self.name] = nodes[:0]
            yield 0, r
        if count < self.max:
            for alt in self.content:
                for c0, r0 in generate_matches(alt, nodes):
                    for c1, r1 in self._recursive_matches(nodes[c0:], count+1):
                        r = {}
                        r.update(r0)
                        r.update(r1)
                        yield c0 + c1, r


def generate_matches(patterns, nodes):
    """Generator yielding matches for a sequence of patterns and nodes.

    Args:
        patterns: a sequence of patterns
        nodes: a sequence of nodes

    Yields:
        (count, results) tuples where:
        count: the entire sequence of patterns matches nodes[:count];
        results: dict containing named submatches.
        """
    if not patterns:
        yield 0, {}
    else:
        p, rest = patterns[0], patterns[1:]
        for c0, r0 in p.generate_matches(nodes):
            if not rest:
                yield c0, r0
            else:
                for c1, r1 in generate_matches(rest, nodes[c0:]):
                    r = {}
                    r.update(r0)
                    r.update(r1)
                    yield c0 + c1, r
