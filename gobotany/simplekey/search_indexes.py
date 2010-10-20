from haystack import indexes
from haystack import site
from gobotany.core.models import Taxon, Family, Genus


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
        cvs = obj.character_values.filter(
            character__short_name=self.character_name)
        if len(cvs) > 0:
            return cvs[0].value
        return None


class TaxonIndex(indexes.SearchIndex):
    scientific_name = indexes.CharField(model_attr='scientific_name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_species.txt')

    # extra non-searchable, retrievable fields, used for display
    description = CharacterCharField(indexed=True,
                                     character_name='description',
                                     default='description not yet available')

    def get_queryset(self):
        return Taxon.objects.filter(simple_key=True)


class FamilyIndex(indexes.SearchIndex):
    name = indexes.CharField(model_attr='name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_family.txt')


class GenusIndex(indexes.SearchIndex):
    name = indexes.CharField(model_attr='name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_genus.txt')


site.register(Taxon, TaxonIndex)
site.register(Family, FamilyIndex)
site.register(Genus, GenusIndex)
