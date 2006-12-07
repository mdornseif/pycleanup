#!/usr/bin/python
	# comment indented by tab
"""Docstring."""
import sys

d = {"x": 42}
if d.has_key("x") or d.has_key("y"):
    print d["x"] + \
          42

def foo():
	pass # body indented by tab

def apply_examples():
    x = apply(f, g + h)
    y = apply(f, g, h)
    z = apply(fs[0], g or h, h or g)
    # Hello
    apply(f, (x, y) + t)
    apply(f, args,)
    apply(f, args, kwds,)
    # Test that complex functions are parenthesized
    x = apply(f+g, args)
    x = apply(f*g, args)
    x = apply(f**g, args)
    # But dotted names etc. not
    x = apply(f.g, args)
    x = apply(f[x], args)
    x = apply(f(), args)
    # Extreme case
    x = apply(a.b.c.d.e.f, args, kwds)
    # XXX Comments in weird places still get lost
    apply(   # foo
          f, # bar
          args)

def bad_apply_examples():
    # These should *not* be touched
    apply()
    apply(f)
    apply(f,)
    apply(f, args, kwds, extras)
    apply(f, *args, **kwds)
    apply(f, *args)
    apply(func=f, args=args, kwds=kwds)
    apply(f, args=args, kwds=kwds)
    apply(f, args, kwds=kwds)

def print_examples():
    # plain vanilla
    print 1, 1+1, 1+1+1
    #
    print 1, 2
    #
    print 1

    print

    # trailing commas
    print 1, 2, 3,
    #
    print 1, 2,
    #
    print 1,
    #
    print

    # >> stuff
    print >>sys.stderr, 1, 2, 3    # no trailing comma
    #
    print >>sys.stdder, 1, 2,      # trailing comma
    #
    print >>sys.stderr, 1+1        # no trailing comma
    #
    print >>  sys.stderr           # spaces before sys.stderr

# This is the last line.
