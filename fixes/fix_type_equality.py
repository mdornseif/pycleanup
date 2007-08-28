"""Change some type comparisons to isinstance() calls:

type(x) == T -> isinstance(x, T)
type(x) is T -> isinstance(x, T)
"""
# Author: Jacques Frechet

# Local imports
from fixes import basefix
from fixes.util import Call, Comma, Name


class FixTypeEquality(basefix.BaseFix):

    PATTERN = """
        comparison< power< 'type' trailer< '(' x=any ')' > > ('==' | 'is') T=any > |
        comparison< T=any ('==' | 'is') power< 'type' trailer< '(' x=any ')' > > >
    """

    def transform(self, node, results):
        x = results['x'].clone() # The thing inside of type()
        T = results['T'].clone() # The type being compared against
        x.set_prefix('')
        T.set_prefix(' ')
        return Call(Name('isinstance', prefix=node.get_prefix()),
                    [x, Comma(), T])
