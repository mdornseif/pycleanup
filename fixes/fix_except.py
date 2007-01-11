"""Fixer for except statements with named exceptions."""

# Python imports
import token
import pprint

# Local imports
import pytree
from fixes import basefix

def get_lineno(node):
    while not isinstance(node, pytree.Leaf):
        if not node.children:
            return
        node = node.children[0]
    return node.lineno
    
def find_excepts(nodes):
    for i in range(len(nodes)):
        n = nodes[i]
        if isinstance(n, pytree.Node):
            if n.children[0].value == 'except':
                yield (n, nodes[i+2])

as_leaf = pytree.Leaf(token.NAME, "as")
as_leaf.set_prefix(" ")

ass_leaf = pytree.Leaf(token.EQUAL, "=")
ass_leaf.set_prefix(" ")

class FixExcept(basefix.BaseFix):

    PATTERN = """
    try_stmt< 'try' ':' suite
                  cleanup=((except_clause ':' suite)+ ['else' ':' suite]
                                                      ['finally' ':' suite]
	                       | 'finally' ':' suite) >
    """
    
    def transform(self, node):
        syms = self.syms
        results = self.match(node)
        assert results
        
        try_cleanup = [ch.clone() for ch in results['cleanup']]
        for except_clause, e_suite in find_excepts(try_cleanup):
            if len(except_clause.children) == 4:
                (E, comma, N) = except_clause.children[1:4]
                comma.replace(as_leaf.clone())
                if str(N).strip()[0] == '(':
                    # We're dealing with a tuple
                    lineno = get_lineno(N)
                    msg = "At line %d, exception unpacking is going away"
                    self.logger.warning(msg % lineno)
                elif N.type != token.NAME:
                    # Generate a new N for the except clause
                    new_N = pytree.Leaf(token.NAME, self.new_name())
                    new_N.set_prefix(" ")
                    target = N.clone()
                    target.set_prefix("")
                    N.replace(new_N)
                    
                    # Insert "old_N = new_N" as the first statement in
                    #  the except body
                    suite_stmts = list(e_suite.children)
                    for i, stmt in enumerate(suite_stmts):
                        if isinstance(stmt, pytree.Node):
                            break
                    assign = pytree.Node(syms.atom,
                                         [target,
                                          ass_leaf.clone(),
                                          new_N.clone()])
                    
                    assign.parent = e_suite                      
                    suite_stmts = suite_stmts[:i] + [assign] + suite_stmts
                    e_suite.children = tuple(suite_stmts)
        
        children = [c.clone() for c in node.children[:3]] + try_cleanup
        return pytree.Node(node.type, children)
