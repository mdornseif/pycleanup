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
import difflib
import optparse

# Local imports
import pytree
import patcomp
from pgen2 import driver
import fixes
import pygram


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
                      help="List available transformations (fixes/fix_*.py)")
    parser.add_option("-v", "--verbose", action="store_true",
                      help="More verbose logging")
    parser.add_option("-w", "--write", action="store_true")

    # Parse command line arguments
    options, args = parser.parse_args(args)
    if options.list_fixes:
        print "Available transformations for the -f/--fix option:"
        for fixname in get_all_fix_names():
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
        rt.summarize()

    # Return error status (0 if rt.errors is zero)
    return int(bool(rt.errors))


def get_all_fix_names():
    """Return a sorted list of all available fix names."""
    fix_names = []
    names = os.listdir(os.path.dirname(fixes.__file__))
    names.sort()
    for name in names:
        if name.startswith("fix_") and name.endswith(".py"):
            fix_names.append(name[4:-3])
    fix_names.sort()
    return fix_names


class RefactoringTool(object):

    def __init__(self, options):
        """Initializer.

        The argument is an optparse.Values instance.
        """
        self.options = options
        self.errors = 0
        self.driver = driver.Driver(pygram.python_grammar,
                                    convert=pytree.convert)
        self.fixers = self.get_fixers()
        self.files = []  # List of files that were or should be modified

    def get_fixers(self):
        """Inspects the options to load the requested patterns and handlers."""
        fixers = []
        fix_names = self.options.fix
        if not fix_names or "all" in fix_names:
            fix_names = get_all_fix_names()
        for fix_name in fix_names:
            try:
                mod = __import__("fixes.fix_" + fix_name, {}, {}, ["*"])
            except ImportError:
                self.log_error("Can't find transformation %s", fix_name)
                continue
            parts = fix_name.split("_")
            class_name = "Fix" + "".join(p.title() for p in parts)
            try:
                fix_class = getattr(mod, class_name)
            except AttributeError:
                self.log_error("Can't find fixes.fix_%s.%s",
                               fix_name, class_name)
                continue
            try:
                fixer = fix_class(self.options)
            except Exception, err:
                self.log_error("Can't instantiate fixes.fix_%s.%s()",
                               fix_name, class_name)
                continue
            if self.options.verbose:
                self.log_message("Adding transformation: %s", fix_name)
            fixers.append(fixer)
        return fixers

    def log_error(self, msg, *args):
        """Increments error count and log a message."""
        self.errors += 1
        self.log_message(msg, *args)

    def log_message(self, msg, *args):
        """Hook to log a message."""
        if args:
            msg = msg % args
        print >>sys.stderr, msg

    def refactor_args(self, args):
        """Refactors files and directories from an argument list."""
        for arg in args:
            if os.path.isdir(arg):
                self.refactor_dir(arg)
            else:
                self.refactor_file(arg)

    def refactor_dir(self, arg):
        """Descends down a directory and refactor every Python file found.

        Python files are assumed to have a .py extension.

        Files and subdirectories starting with '.' are skipped.
        """
        for dirpath, dirnames, filenames in os.walk(arg):
            if self.options.verbose:
                self.log_message("Descending into %s", dirpath)
            dirnames.sort()
            filenames.sort()
            for name in filenames:
                if not name.startswith(".") and name.endswith("py"):
                    fullname = os.path.join(dirpath, name)
                    self.refactor_file(fullname)
            # Modify dirnames in-place to remove subdirs with leading dots
            dirnames[:] = [dn for dn in dirnames if not dn.startswith(".")]

    def refactor_file(self, filename):
        """Refactors a file."""
        try:
            f = open(filename)
        except IOError, err:
            self.log_error("Can't open %s: %s", filename, err)
            return
        try:
            try:
                tree = self.driver.parse_file(filename)
            except Exception, err:
                self.log_error("Can't parse %s: %s: %s",
                               filename, err.__class__.__name__, err)
                return
            if self.options.verbose:
                self.log_message("Refactoring %s", filename)
            if self.refactor_tree(tree):
                self.write_tree(tree, filename)
            elif self.options.verbose:
                self.log_message("No changes in %s", filename)
        finally:
            f.close()

    def refactor_tree(self, tree):
        """Refactors a parse tree."""
        changes = 0
        for node in tree.post_order():
            for fixer in self.fixers:
                if fixer.match(node):
                    new = fixer.transform(node)
                    if new is not None and new != node:
                        node.replace(new)
                        changes += 1
        return changes

    def write_tree(self, tree, filename):
        """Writes a (presumably modified) tree to a file.

        If there are no changes, this is a no-op.

        Otherwise, it first shows a unified diff between the old file
        and the tree, and then rewrites the file, but the latter is
        only done if the write option is set.
        """
        self.files.append(filename)
        try:
            f = open(filename, "r")
        except IOError, err:
            self.log_error("Can't read %s: %s", filename, err)
            return
        try:
            old_text = f.read()
        finally:
            f.close()
        new_text = str(tree)
        if old_text == new_text:
            if self.options.verbose:
                self.log_message("No changes to %s", filename)
            return
        diff_texts(old_text, new_text, filename)
        if not self.options.write:
            if self.options.verbose:
                self.log_message("Not writing changes to %s", filename)
            return
        backup = filename + ".bak"
        if os.path.lexists(backup):
            try:
                os.remove(backup)
            except os.error, err:
                self.log_message("Can't remove backup %s", backup)
        try:
            os.rename(filename, backup)
        except os.error, err:
            self.log_message("Can't rename %s to %s", filename, backup)
        try:
            f = open(filename, "w")
        except os.error, err:
            self.log_error("Can't create %s: %s", filename, err)
            return
        try:
            try:
                f.write(new_text)
            except os.error, err:
                self.log_error("Can't write %s: %s", filename, err)
        finally:
            f.close()
        if self.options.verbose:
            self.log_message("Wrote changes to %s", filename)

    def summarize(self):
        if not self.files:
            self.log_message("No files were (or should be) modified.")
        else:
            self.log_message("Files that were (or should be) modified:")
            for file in self.files:
                self.log_message(file)
        if self.errors:
            if self.errors == 1:
                self.log_message("There was 1 error")
            else:
                self.log_message("There were %d errors", self.errors)


def diff_texts(a, b, filename):
    a = a.splitlines()
    b = b.splitlines()
    for line in difflib.unified_diff(a, b, filename, filename,
                                     "(original)", "(refactored)",
                                     lineterm=""):
        print line


if __name__ == "__main__":
  sys.exit(main())
