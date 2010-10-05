from haystack import indexes
from haystack import site
from gobotany.core.models import Taxon


class CharacterCharField(indexes.CharField):
    '''A CharField that understands how to get the character value
    from a taxon model instance.
    '''

    def __init__(self, character_name=None,
                 document=False, indexed=True, stored=True,
                 default=indexes.NOT_PROVIDED, null=False):
        super(CharacterCharField, self).__init__(model_attr=None,
                                                 use_template=False,
                                                 template_name=False,
                                                 document=document,
                                                 indexed=indexed,
                                                 stored=stored,
                                                 default=default,
                                                 null=null)
        self.character_name = character_name
        assert character_name is not None, 'character_name cannot be None'

    def prepare(self, obj):
        return self.convert(self.lookup_character_value(obj) or self.default)

    def lookup_character_value(self, obj):
        return None


class TaxonIndex(indexes.SearchIndex):
    scientific_name = indexes.CharField(model_attr='scientific_name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_taxon.txt')

    # extra non-searchable, retrievable fields, used for display
    description = CharacterCharField(indexed=True,
                                     character_name='description',
                                     default='description not yet imported')

    def get_queryset(self):
        return Taxon.objects.filter(simple_key=True)


site.register(Taxon, TaxonIndex)
