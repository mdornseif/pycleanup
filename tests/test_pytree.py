#!/usr/bin/env python2.5
# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Unit tests for pytree.py.

NOTE: Please *don't* add doc strings to individual test methods!
In verbose mode, printing of the module, class and method name is much
more helpful than printing of (the first line of) the docstring,
especially when debugging a test.
"""

# Testing imports
import support
if __name__ == '__main__':
    support.adjust_path()

# Local imports (XXX should become a package)
import pytree


class TestNodes(support.TestCase):

    """Unit tests for nodes (Base, Leaf, Node)."""

    def testBaseCantConstruct(self):
        if __debug__:
            # Test that instantiating Base() raises an AssertionError
            self.assertRaises(AssertionError, pytree.Base)

    def testLeaf(self):
        l1 = pytree.Leaf(100, "foo")
        self.assertEqual(l1.type, 100)
        self.assertEqual(l1.value, "foo")

    def testLeafRepr(self):
        l1 = pytree.Leaf(100, "foo")
        self.assertEqual(repr(l1), "Leaf(100, 'foo')")

    def testLeafStr(self):
        l1 = pytree.Leaf(100, "foo")
        self.assertEqual(str(l1), "foo")
        l2 = pytree.Leaf(100, "foo", context=(" ", (10, 1)))
        self.assertEqual(str(l2), " foo")

    def testLeafEq(self):
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(100, "foo", context=(" ", (1, 0)))
        self.assertEqual(l1, l2)
        l3 = pytree.Leaf(101, "foo")
        l4 = pytree.Leaf(100, "bar")
        self.assertNotEqual(l1, l3)
        self.assertNotEqual(l1, l4)

    def testLeafPrefix(self):
        l1 = pytree.Leaf(100, "foo")
        self.assertEqual(l1.get_prefix(), "")
        l1.set_prefix("  ##\n\n")
        self.assertEqual(l1.get_prefix(), "  ##\n\n")

    def testNode(self):
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(200, "bar")
        n1 = pytree.Node(1000, [l1, l2])
        self.assertEqual(n1.type, 1000)
        self.assertEqual(n1.children, (l1, l2))

    def testNodeRepr(self):
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(100, "bar", context=(" ", (1, 0)))
        n1 = pytree.Node(1000, [l1, l2])
        self.assertEqual(repr(n1),
                         "Node(1000, (%s, %s))" % (repr(l1), repr(l2)))

    def testNodeStr(self):
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(100, "bar", context=(" ", (1, 0)))
        n1 = pytree.Node(1000, [l1, l2])
        self.assertEqual(str(n1), "foo bar")

    def testNodePrefix(self):
        l1 = pytree.Leaf(100, "foo")
        self.assertEqual(l1.get_prefix(), "")
        n1 = pytree.Node(1000, [l1])
        self.assertEqual(n1.get_prefix(), "")
        n1.set_prefix(" ")
        self.assertEqual(n1.get_prefix(), " ")
        self.assertEqual(l1.get_prefix(), " ")

    def testNodeEq(self):
        n1 = pytree.Node(1000, ())
        n2 = pytree.Node(1000, [], context=(" ", (1, 0)))
        self.assertEqual(n1, n2)
        n3 = pytree.Node(1001, ())
        self.assertNotEqual(n1, n3)

    def testNodeEqRecursive(self):
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(100, "foo")
        n1 = pytree.Node(1000, [l1])
        n2 = pytree.Node(1000, [l2])
        self.assertEqual(n1, n2)
        l3 = pytree.Leaf(100, "bar")
        n3 = pytree.Node(1000, [l3])
        self.assertNotEqual(n1, n3)

    def testReplace(self):
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(100, "+")
        l3 = pytree.Leaf(100, "bar")
        n1 = pytree.Node(1000, [l1, l2, l3])
        self.assertEqual(n1.children, (l1, l2, l3))
        l2new = pytree.Leaf(100, "-")
        l2.replace(l2new)
        self.assertEqual(n1.children, (l1, l2new, l3))

    def testConvert(self):
        # XXX
        pass


class TestPatterns(support.TestCase):

    """Unit tests for tree matching patterns."""

    def testBasicPatterns(self):
        # Build a tree
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(100, "bar")
        l3 = pytree.Leaf(100, "foo")
        n1 = pytree.Node(1000, [l1, l2])
        n2 = pytree.Node(1000, [l3])
        root = pytree.Node(1000, [n1, n2])
        # Build a pattern matching a leaf
        pl = pytree.LeafPattern(100, "foo", name="pl")
        r = {}
        self.assertEqual(pl.match(root, results=r), False)
        self.assertEqual(r, {})
        self.assertEqual(pl.match(n1, results=r), False)
        self.assertEqual(r, {})
        self.assertEqual(pl.match(n2, results=r), False)
        self.assertEqual(r, {})
        self.assertEqual(pl.match(l1, results=r), True)
        self.assertEqual(r, {"pl": l1})
        r = {}
        self.assertEqual(pl.match(l2, results=r), False)
        self.assertEqual(r, {})
        # Build a pattern matching a node
        pn = pytree.NodePattern(1000, [pl], name="pn")
        self.assertEqual(pn.match(root, results=r), False)
        self.assertEqual(r, {})
        self.assertEqual(pn.match(n1, results=r), False)
        self.assertEqual(r, {})
        self.assertEqual(pn.match(n2, results=r), True)
        self.assertEqual(r, {"pn": n2, "pl": l3})
        r = {}
        self.assertEqual(pn.match(l1, results=r), False)
        self.assertEqual(r, {})
        self.assertEqual(pn.match(l2, results=r), False)
        self.assertEqual(r, {})

    def testWildcardPatterns(self):
        # Build a tree for testing
        l1 = pytree.Leaf(100, "foo")
        l2 = pytree.Leaf(100, "bar")
        l3 = pytree.Leaf(100, "foo")
        n1 = pytree.Node(1000, [l1, l2])
        n2 = pytree.Node(1000, [l3])
        root = pytree.Node(1000, [n1, n2])
        # Build a pattern
        pl = pytree.LeafPattern(100, "foo", name="pl")
        pn = pytree.NodePattern(1000, [pl], name="pn")
        pw = pytree.WildcardPattern([[pn], [pl, pl]], name="pw")
        r = {}
        self.assertEqual(pw.match_seq([root], r), False)
        self.assertEqual(r, {})
        self.assertEqual(pw.match_seq([n1], r), False)
        self.assertEqual(r, {})
        self.assertEqual(pw.match_seq([n2], r), True)
        # These are easier to debug
        self.assertEqual(sorted(r.keys()), ["pl", "pn", "pw"])
        self.assertEqual(r["pl"], l1)
        self.assertEqual(r["pn"], n2)
        self.assertEqual(r["pw"], (n2,))
        # But this is equivalent
        self.assertEqual(r, {"pl": l1, "pn": n2, "pw": (n2,)})
        r = {}
        self.assertEqual(pw.match_seq([l1, l3], r), True)
        self.assertEqual(r, {"pl": l3, "pw": (l1, l3)})
        self.assert_(r["pl"] is l3)
        r = {}

    def testGenerateMatches(self):
        la = pytree.Leaf(1, "a")
        lb = pytree.Leaf(1, "b")
        lc = pytree.Leaf(1, "c")
        ld = pytree.Leaf(1, "d")
        le = pytree.Leaf(1, "e")
        lf = pytree.Leaf(1, "f")
        leaves = [la, lb, lc, ld, le, lf]
        root = pytree.Node(1000, leaves)
        pa = pytree.LeafPattern(1, "a", "pa")
        pb = pytree.LeafPattern(1, "b", "pb")
        pc = pytree.LeafPattern(1, "c", "pc")
        pd = pytree.LeafPattern(1, "d", "pd")
        pe = pytree.LeafPattern(1, "e", "pe")
        pf = pytree.LeafPattern(1, "f", "pf")
        pw = pytree.WildcardPattern([[pa, pb, pc], [pd, pe],
	                             [pa, pb], [pc, pd], [pe, pf]],
                                    min=1, max=4, name="pw")
        self.assertEqual([x[0] for x in pw.generate_matches(leaves)],
	                 [3, 5, 2, 4, 6])
        pr = pytree.NodePattern(type=1000, content=[pw], name="pr")
        matches = list(pytree.generate_matches([pr], [root]))
        self.assertEqual(len(matches), 1)
        c, r = matches[0]
        self.assertEqual(c, 1)
        self.assertEqual(str(r["pr"]), "abcdef")
        self.assertEqual(r["pw"], (la, lb, lc, ld, le, lf))
        for c in "abcdef":
            self.assertEqual(r["p" + c], pytree.Leaf(1, c))

    def testHasKeyExample(self):
        pattern = pytree.NodePattern(331,
                                     (pytree.LeafPattern(7),
                                      pytree.WildcardPattern(name="args"),
                                      pytree.LeafPattern(8)))
        l1 = pytree.Leaf(7, "(")
        l2 = pytree.Leaf(3, "x")
        l3 = pytree.Leaf(8, ")")
        node = pytree.Node(331, (l1, l2, l3))
        r = {}
        self.assert_(pattern.match(node, r))
        self.assertEqual(r["args"], (l2,))


if __name__ == "__main__":
    import __main__
    support.run_all_tests(__main__)