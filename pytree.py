# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Python syntax tree definitions.

There are two concrete classes: Node, which represents an interior
node, and Leaf, which represents a leaf node.

The Base class is an abstract base class that provides some default
functionality and boilerplate using the template pattern.
"""

__author__ = "Guido van Rossum <guido@python.org>"


class Base(object):

    parent = None
    children = ()

    def __new__(cls, *args, **kwds):
        assert cls is not Base, "Cannot instantiate Base"
        return object.__new__(cls, *args, **kwds)

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self._eq(other)

    def __ne__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return not self._eq(other)

    def _eq(self, other):
        raise NotImplementedError

    def set_prefix(self, prefix):
        raise NotImplementedError

    def get_prefix(self):
        raise NotImplementedError


class Node(Base):

    def __init__(self, type, children, context=None):
        self.type = type
        self.children = tuple(children)
        for ch in self.children:
            ch.parent = self

    def __repr__(self):
        return "%s(<>, %r, %r)" % (self.__class__.__name__,
                                   self.type,
                                   self.children)

    def __str__(self):
        return "".join(str(ch) for ch in self.children)

    def _eq(self, other):
        return (self.type, self.children) == (other.type, other.children)

    def set_prefix(self, prefix):
        if self.children:
            self.children[0].set_prefix(prefix)

    def get_prefix(self):
        if not self.children:
            return ""
        return self.children[0].get_prefix()

    def replace(self, new):
        if self is new:
            return
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

    lineno = column = 0

    def __init__(self, type, value, context=None):
        if context is not None:
            self.prefix, (self.lineno, self.column) = context
        else:
            self.prefix = ""
            self.lineno = self.column = 0
        self.type = type
        self.value = value

    def __repr__(self):
        return "%s(<>, %r, %r)" % (self.__class__.__name__,
                                   self.type,
                                   self.value)

    def __str__(self):
        return self.prefix + self.value

    def _eq(self, other):
        return (self.type, self.value) == (other.type, other.value)

    def set_prefix(self, prefix):
        self.prefix = prefix

    def get_prefix(self):
        return self.prefix


def convert(gr, raw_node):
    type, value, context, children = raw_node
    if children or type in gr.number2symbol:
        return Node(type, children, context=context)
    else:
        return Leaf(type, value, context=context)
