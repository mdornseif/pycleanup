#!/usr/bin/env python2.5
# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Refactoring framework.

Used as a main program, this can refactory any number of files and/or
recursively descend down directories.  Imported as a module, this
provides infrastructure to write your own refactoring tool.
"""

__author__ = "Guido van Rossum <guido@python.org>"


# Python imports
import os
import sys
import optparse
import tempfile

# Local imports
import pytree
import patcomp
from pgen2 import driver


def main(args=None):
    """Main program.

    Call without arguments to use sys.argv[1:] as the arguments; or
    call with a list of arguments (excluding sys.argv[0]).

    Returns a suggested exit status (0, 1, 2).
    """
    # Set up option parser
    parser = optparse.OptionParser(usage="refactor.py [options] file|dir ...")
    parser.add_option("-f", "--fix", action="append", default=[],
                      help="Each FIX specifies a transformation; default all")
    parser.add_option("-l", "--list-fixes", action="store_true",
                      help="List available transformations")
    parser.add_option("-v", "--verbose", action="store_true",
                      help="More verbose logging")

    # Parse command line arguments
    options, args = parser.parse_args(args)
    if options.list_fixes:
        print "Available transformations for the -f/--fix option:"
        for fixname in get_all_fixes():
            print fixname
        if not args:
            return 0
    if not args:
        print >>sys.stderr, "At least one file or directory argument required."
        print >>sys.stderr, "Use --help to show usage."
        return 2

    # Initialize the refactoring tool
    rt = RefactoringTool(options)

    # Refactor all files and directories passed as arguments
    if not rt.errors:
        rt.refactor_args(args)

    # Return error status (0 if rt.errors is zero)
    return int(bool(rt.errors))


def get_all_fixes():
    """Return a sorted list of all available fixes."""
    fixes = []
    for name in os.listdir(os.path.dirname(__file__)):
        if name.startswith("fix_") and name.endswith(".py"):
            fixes.append(name[4:-3])
    fixes.sort()
    return fixes


class RefactoringTool(object):

    def __init__(self, options):
        """Initializer.

        The argument is an optparse.Values instance.
        """
        self.options = options
        self.errors = 0
        self.gr = driver.load_grammar("Grammar.txt")
        self.dr = dr = driver.Driver(self.gr, convert=pytree.convert)
        self.pairs = self.get_refactoring_pairs()

    def get_refactoring_pairs(self):
        """Inspects the options to load the requested patterns and handlers."""
        pairs = []
        fixes = self.options.fix
        if not fixes or "all" in fixes:
            fixes = get_all_fixes()
        for fixname in fixes:
            try:
                mod = __import__("fix_" + fixname)
            except (ImportError, AttributeError):
                self.log_error("Can't find transformation %s", fixname)
            else:
                name = "?"
                try:
                    name = "p_" + fixname
                    pattern = getattr(mod, name)
                    name = "fix_" + fixname
                    handler = getattr(mod, name)
                except AttributeError:
                    self.log_error("Can't find fix_%s.%s", fixname, name)
                else:
                    if self.options.verbose:
                        self.log_message("adding transformation: %s", fixname)
                    pairs.append((pattern, handler))
        return pairs

    def log_error(self, msg, *args):
        """Increment error count and log a message."""
        self.errors += 1
        self.log_message(msg, *args)

    def log_message(self, msg, *args):
        """Hook to log a message."""
        if args:
            msg = msg % args
        print >>sys.stderr, msg

    def refactor_args(self, args):
        """Refactor files and directories from an argument list."""
        for arg in args:
            if os.path.isdir(arg):
                self.refactor_dir(arg)
            else:
                self.refactor_file(arg)

    def refactor_dir(self, arg):
        """Descend down a directory and refactor every Python file found.

        Python files are assumed to have a .py extension.

        Files and subdirectories starting with '.' are skipped.
        """
        for dirpath, dirnames, filenames in os.walk(arg):
            if self.options.verbose:
                self.log_message("Descending into %s", dirpath)
            for name in filenames:
                if not name.startswith(".") and name.endswith("py"):
                    fullname = os.path.join(dirpath, name)
                    self.refactor_file(fullname)
            # Modify dirnames in-place to remove subdirs with leading dots
            dirnames[:] = [dn for dn in dirnames if not dn.startswith(".")]

    def refactor_file(self, filename):
        """Refactor a file."""
        try:
            f = open(filename)
        except IOError, err:
            self.log_error("Can't open %s: %s", filename, err)
            return
        try:
            try:
                tree = self.dr.parse_file(filename)
            except Exception, err:
                self.log_error("Can't parse %s: %s: %s",
                               filename, err.__class__.__name__, err)
                return
            if self.options.verbose:
                self.log_message("Refactoring %s", filename)
            if self.refactor_tree(tree):
                self.save_tree(tree, filename)
        finally:
            f.close()

    def refactor_tree(self, tree):
        changes = 0
        for node in tree.post_order():
            for pattern, handler in self.pairs:
                if pattern.match(node):
                    # XXX Change handler API to return a replacement node
                    handler(node)
                    changes += 1
        return changes

    def save_tree(self, tree, filename):
        """Save a (presumably modified) tree to a file.

        Skip the saving if no changes were made.

        XXX For now, don't save, just print a unified diff.
        """
        tfn = tempfile.mktemp()
        f = open(tfn, "w")
        try:
            try:
                f.write(str(tree))
            finally:
                f.close()
            sts = os.system("diff -u %s %s" % (filename, tfn))
            if sts == 0:
                pass # No changes
            elif sts == 1<<8:
                # XXX Actually save it
                pass
            else:
                self.log_error("diff %s returned exit (%s,%s)",
                               filename, sts>>8, sts&0xFF)
        finally:
            os.remove(tfn)


if __name__ == "__main__":
  sys.exit(main())
