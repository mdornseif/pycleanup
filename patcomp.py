# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Pattern compiler.

The grammer is taken from PatternGrammar.txt.

The compiler compiles a pattern to a pytree.*Pattern instance.
"""

__author__ = "Guido van Rossum <guido@python.org>"

# Python tokens
import sys
import token

# Fairly local imports
from pgen2 import driver
from pgen2 import literals

# Really local imports
import pytree


class Symbols(object):

    def __init__(self, grammar):
        """Initializer.

        Creates an attribute for each grammar symbol (nonterminal),
        whose value is the symbol's type (an int >= 256).
        """
        self._grammar = grammar
        for name in grammar.symbol2number:
            setattr(self, name, grammar.symbol2number[name])


class PatternCompiler(object):

    def __init__(self, grammar_file="PatternGrammar.txt"):
        """Initializer.

        Takes an optional alternative filename for the pattern grammar.
        """
        self.grammar = driver.load_grammar(grammar_file)
        self.syms = Symbols(self.grammar)
        self.pygrammar = driver.load_grammar("Grammar.txt")
        self.pysyms = Symbols(self.pygrammar)
        self.driver = driver.Driver(self.grammar, convert=pattern_convert)

    def compile_pattern(self, input, debug=False):
        """Compiles a pattern string to a nested pytree.*Pattern object."""
        root = self.driver.parse_string(input, debug=debug)
        return self.compile_node(root)

    def compile_node(self, node):
        """Compiles a node, recursively.

        This is one big switch on the node type.
        """
        # XXX Leave the optimizations to later
        if node.type == self.syms.Matcher:
            node = node.children[0] # Avoid unneeded recursion

        if node.type == self.syms.Alternatives:
            # Skip the odd children since they are just '|' tokens
            alts = [self.compile_node(ch) for ch in node.children[::2]]
            return pytree.WildcardPattern([[a] for a in alts], min=1, max=1)

        if node.type == self.syms.Alternative:
            units = [self.compile_node(ch) for ch in node.children]
            return pytree.WildcardPattern([units], min=1, max=1)

        if node.type == self.syms.NegatedUnit:
            pattern = self.compile_basic(node.children[1:])
            return pytree.NegatedPattern(pattern)

        assert node.type == self.syms.Unit

        name = None
        nodes = node.children
        if len(nodes) >= 3 and nodes[1].type == token.EQUAL:
            name = nodes[0].value
            nodes = nodes[2:]
        repeat = None
        if len(nodes) >= 2 and nodes[-1].type == self.syms.Repeater:
            repeat = nodes[-1]
            nodes = nodes[:-1]

        # Now we've reduced it to: STRING | NAME [Details] | (...) | [...]
        pattern = self.compile_basic(nodes, repeat)

        if repeat is not None:
            assert repeat.type == self.syms.Repeater
            children = repeat.children
            child = children[0]
            if child.type == token.STAR:
                min = 0
                max = sys.maxint
            elif child.type == token.PLUS:
                min = 1
                max = sys.maxint
            else:
                assert len(children) == 5
                assert child.type == token.LBRACE
                min = self.get_int(children[1])
                max = self.get_int(children[3])
            pattern = pytree.WildcardPattern([[pattern]], min=min, max=max)
        if name is not None:
            pattern.name = name
        return pattern

    def compile_basic(self, nodes, repeat=None):
        # Compile STRING | NAME [Details] | (...) | [...]
        assert len(nodes) >= 1
        node = nodes[0]
        if node.type == token.STRING:
            value = literals.evalString(node.value)
            return pytree.LeafPattern(content=value)
        elif node.type == token.NAME:
            value = node.value
            if value.isupper():
                if value not in TOKEN_MAP:
                    raise SyntaxError("Invalid token: %r" % value)
                return pytree.LeafPattern(TOKEN_MAP[value])
            else:
                if value == "any":
                    type = None
                elif not value.startswith("_"):
                    type = getattr(self.pysyms, value, None)
                    if type is None:
                        raise SyntaxError("Invalid symbol: %r" % value)
                if nodes[1:]: # Details present
                    content = [self.compile_node(nodes[1].children[1])]
                else:
                    content = None
                return pytree.NodePattern(type, content)
        elif node.value == "(":
            return self.compile_node(nodes[1])
        elif node.value == "[":
            assert repeat is None
            subpattern = self.compile_node(nodes[1])
            return pytree.WildcardPattern([[subpattern]], min=0, max=1)
        assert False, node

    def get_int(self, node):
        assert node.type == token.NUMBER
        return int(node.value)


# Map named tokens to the type value for a LeafPattern
TOKEN_MAP = {"NAME": token.NAME,
             "STRING": token.STRING,
             "NUMBER": token.NUMBER,
             "TOKEN": None}


def pattern_convert(grammar, raw_node_info):
    """Converts raw node information to a Node or Leaf instance."""
    type, value, context, children = raw_node_info
    if children or type in grammar.number2symbol:
        return pytree.Node(type, children, context=context)
    else:
        return pytree.Leaf(type, value, context=context)


def test():
    pc = PatternCompiler()
    pat = pc.compile_pattern("a=power< 'apply' trailer<'(' b=(not STRING) ')'> >")
    print pat


if __name__ == "__main__":
    test()
