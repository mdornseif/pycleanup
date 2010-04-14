"""Fixer that changes 'a ,b' into 'a, b'.

This also changes '{a :b}' into '{a: b}', but does not touch other
uses of colons.  It does not touch other uses of whitespace.

"""

from .. import pytree
from ..pgen2 import token
from .. import fixer_base


#     response = render_to_response('pressespiegel/pressclipping_archive.html',
#                                  {'language': request.LANGUAGE_CODE.split('-')[0],'latest': latest_press},
#                                  context_instance=RequestContext(request))


class FixWsComma(fixer_base.BaseFix):

    explicit = True # The user must ask for this fixers

    PATTERN = """
    any<(not(',') any)+ ',' ((not(',') any)+ ',')* [not(',') any]>
    """
    #[^,]+,([^,]+,)*[^,]+

    COMMA = pytree.Leaf(token.COMMA, u",")
    COLON = pytree.Leaf(token.COLON, u":")
    SEPS = (COMMA, COLON)

    def transform(self, node, results):
        new = node.clone()
        comma = False
        for child in new.children:
            if child in self.SEPS:
                prefix = child.prefix
                if prefix.isspace() and u"\n" not in prefix:
                    child.prefix = u""
                comma = True
            else:
                if comma:
                    prefix = child.prefix
                    if not prefix or (prefix.isspace() and u"\n" not in prefix):
                        prefix = u" "
                    child.prefix = prefix
                comma = False
        return new
