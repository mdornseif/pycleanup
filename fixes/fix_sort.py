"""Change the two-line list/sort idiom into the modern sorted() call.

That is, both

    v = list(t())
    v.sort()
    foo(v)

and

    v = t()
    v.sort()
    foo(v)
    
becomes

    v = sorted(t())
    foo(v)
"""
# Author: Collin Winter

# Local imports
from fixes import basefix
from fixes.util import Name, Call


class FixSort(basefix.BaseFix):

    PATTERN = r"""
              any<
                  any*
                  simple_stmt<
                    expr_stmt< id1=any '='
                               power< list='list' trailer< '(' (not arglist<any+>) any ')' > >
                    >
                    '\n'
                  >
                  sort=
                  simple_stmt<
                    power< id2=any
                           trailer< '.' 'sort' > trailer< '(' ')' >
                    >
                    '\n'
                  >
                  next=any*
              >
              |
              any<
                  any*
                  simple_stmt< expr_stmt< id1=any '=' expr=any > '\n' >
                  sort=
                  simple_stmt<
                    power< id2=any
                           trailer< '.' 'sort' > trailer< '(' ')' >
                    >
                    '\n'
                  >
                  next=any*
              >
              """

    def match(self, node):
        r = super(FixSort, self).match(node)
        if r:
            if r["id1"] == r["id2"]:
                return r
            return None
        return r

    def transform(self, node, results):
        sort_stmt = results["sort"]
        next_stmt = results["next"]
        list_call = results.get("list")
        simple_expr = results.get("expr")

        if list_call:
            list_call.replace(Name("sorted", prefix=list_call.get_prefix()))
        elif simple_expr:
            new = simple_expr.clone()
            new.set_prefix("")
            simple_expr.replace(Call(Name("sorted"), [new],
                                     prefix=simple_expr.get_prefix()))
        else:
            raise RuntimeError("should not have reached here")
        sort_stmt.remove()
        if next_stmt:
            next_stmt[0].set_prefix(sort_stmt.get_prefix())
