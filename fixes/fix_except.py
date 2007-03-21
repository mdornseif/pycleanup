"""Fixer for except statements with named exceptions.

The following cases will be converted:

- "except E, T:" where T is a name:
    
    except E as T:
    
- "except E, T:" where T is not a name, tuple or list:
    
        except E as t:
            T = t
        
    This is done because the target of an "except" clause must be a
    name.
    
- "except E, T:" where T is a tuple or list literal:
    
        except E as t:
            T = t.message
    
    This transformation is still under consideration.
"""
# Author: Collin Winter

# Local imports
import pytree
from pgen2 import token
from fixes import basefix
from fixes.util import Assign, Attr, Name

def find_excepts(nodes):
    for i, n in enumerate(nodes):
        if isinstance(n, pytree.Node):
            if n.children[0].value == 'except':
                yield (n, nodes[i+2])

### Common across all transforms
as_leaf = pytree.Leaf(token.NAME, "as")
as_leaf.set_prefix(" ")

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
                if N.type != token.NAME:
                    # Generate a new N for the except clause
                    new_N = Name(self.new_name(), prefix=" ")
                    target = N.clone()
                    target.set_prefix("")
                    N.replace(new_N)
                    new_N = new_N.clone()

                    # Insert "old_N = new_N" as the first statement in
                    #  the except body. This loop skips leading whitespace
                    #  and indents
                    suite_stmts = list(e_suite.children)
                    for i, stmt in enumerate(suite_stmts):
                        if isinstance(stmt, pytree.Node):
                            break

                    # The assignment is different if old_N is a tuple
                    # In that case, the assignment is old_N = new_N.message
                    if str(N).strip()[0] == '(':
                        assign = Assign(target, Attr(new_N, Name('message')))
                    else:
                        assign = Assign(target, new_N)

                    assign.parent = e_suite
                    suite_stmts = suite_stmts[:i] + [assign] + suite_stmts
                    e_suite.children = tuple(suite_stmts)

        children = [c.clone() for c in node.children[:3]] + try_cleanup
        return pytree.Node(node.type, children)
