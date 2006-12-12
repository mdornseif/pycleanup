#!/usr/bin/env python2.5
# Copyright 2006 Google Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Null refactoring."""

import patcomp

pat_compile = patcomp.PatternCompiler().compile_pattern
p_null = pat_compile("'?'")

def fix_null(node):
    pass
