# Copyright 2004-2005 Elemental Security, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

# Modifications:
# Copyright 2006 Python Software Foundation. All Rights Reserved.

def test():
    import sys
    sys.path[0] = ".."
    from pgen2 import astnode, driver
    f = open("Grammar.txt", "w")
    try:
        astnode.generate_grammar(f)
    finally:
        f.close()
    sample = "year<=1989 ? ('Modula-3' + ABC) ** 2 : Python"
    dr = driver.Driver(driver.load_grammar())
    tree = dr.parse_string(sample, True)
    print tree

if __name__ == "__main__":
    test()
