"""Fixer that changes 'a ,b' into 'a, b'.

This also changes '{a :b}' into '{a: b}', but does not touch other
uses of colons.  It does not touch other uses of whitespace.

"""

from .. import pytree
from ..pgen2 import token
from .. import fixer_base

from ..pygram import python_symbols as syms

class FixWsEqual(fixer_base.BaseFix):

    explicit = False

    PATTERN = """
    any<(not('=') any)+ '=' (not('=') any)>
    """

    # TODO:
    # return HttpResponseRedirect(Product.objects.get(artnr= artnrs[0]).get_public_url())
    # kaufdatum = models.CharField(max_length= 64) # DateField
    # def find_related_faqs_helper(faq, cutoff= 0.4):
    # ret.append(Faq.objects.get(id= faqid))
    # def extract_keywords_textrank(content, num_terms= 20, num_terms2= 20):

   #class FaqAdmin(admin.ModelAdmin):
   #    list_display = ['question']
   #    list_filter = ['updated_at']
   #    search_fields = ['question', 'answer']
   #    save_on_top=True
   #    prepopulated_fields = {"slug": ("question",)}
   ##    raw_id_fields = ['products']


    EQUAL = pytree.Leaf(token.EQUAL, u"=")

    def transform(self, node, results):
        new = node.clone()
        is_assignment = False
        seenequal = False
        for child in new.children:
            if child == self.EQUAL:
                prefix = child.prefix
                if prefix.isspace() and u"\n" not in prefix:
                    if not node.parent.type not in (syms.arglist, syms.trailer):
                        child.prefix = u""
                    else:
                        is_assignment = True
                        child.prefix = u" "
                seenequal = True
            else:
                if seenequal:
                    prefix = child.prefix
                    if not prefix or (prefix.isspace() and u"\n" not in prefix):
                        if is_assignment:
                            child.prefix = u" "
                        else:
                            child.prefix = u""
                seenequal = False
        return new
