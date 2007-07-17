"""StringIO.StringIO -> io.StringIO (imports, too).

Imports this fixer picks up on:
* "import StringIO" -> "import io"
* "from StringIO import StringIO" -> "from io import StringIO"
* "import StringIO as foo" -> "import io as foo"

If the fixer finds "import StringIO", all "StringIO.StringIO" attribute
lookups will be translated to "io.StringIO" and all "StringIO" names
will be translated to "io".
"""
# Author: Collin Winter

# Local imports
from fixes import basefix
from fixes.util import Name, attr_chain, any


class FixStringio(basefix.BaseFix):
    PATTERN = """
    import_name< 'import' (module='StringIO'
                           | dotted_as_names< any* module='StringIO' any* >) >
    |
    import_from< 'from' module_name='StringIO' 'import'
                 ( 'StringIO' | import_as_name< 'StringIO' 'as' any >) >
    |
    import_from< 'from' module_name='StringIO' 'import' star='*' >
    |
    import_name< 'import' dotted_as_name< module_name='StringIO' 'as' any > >
    |
    power< module_name='StringIO' trailer< '.' 'StringIO' > any* >
    |
    bare_name='StringIO'
    """

    order = "pre" # Pre-order tree traversal

    # Don't match 'StringIO' if it's within another match
    def match(self, node):
        match = super(FixStringio, self).match
        results = match(node)
        if results:
            if any([match(obj) for obj in attr_chain(node.parent, "parent")]):
                return False
            return results
        return False

    def start_tree(self, tree, filename):
        super(FixStringio, self).start_tree(tree, filename)
        self.module_import = False

    def transform(self, node, results):
        import_mod = results.get("module")
        module_name = results.get("module_name")
        bare_name = results.get("bare_name")
        star = results.get("star")

        if import_mod:
            self.module_import = True
            import_mod.replace(Name("io", prefix=import_mod.get_prefix()))
        elif module_name:
            module_name.replace(Name("io", prefix=module_name.get_prefix()))
            if star:
                star.replace(Name("StringIO", prefix=star.get_prefix()))
        elif bare_name and self.module_import:
            bare_name.replace(Name("io", prefix=bare_name.get_prefix()))