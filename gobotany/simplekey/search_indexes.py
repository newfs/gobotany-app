from haystack import indexes
from haystack import site

from gobotany.core.models import Taxon, Family, Genus, GlossaryTerm

from gobotany.simplekey.models import (PlainPage,
                                       GroupsListPage, SubgroupResultsPage,
                                       SubgroupsListPage)

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


class BaseIndex(indexes.SearchIndex):
    """A document that already knows its URL, so searches render faster."""

    url = indexes.CharField(use_template=True,
                            template_name='simplekey/search_url.txt')

    def read_queryset(self):
        """Bypass `index_queryset()` when we just need to read a model.

        The `SearchIndex` method `read_queryset()` is simply a fallback
        to the `index_queryset()` method.  But since we tend to festoon
        our index query-sets with all sorts of pre-loading that makes
        indexing faster, we need to prevent `read_queryset()` from
        falling back so that its reads remain simple.

        """
        # Copied from base class index_queryset():

        return self.model._default_manager.all()


class TaxonIndex(BaseIndex):
    name = indexes.CharField(model_attr='scientific_name')
    title = indexes.CharField(use_template=True,
        template_name='simplekey/search_title_species.txt')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_species.txt')

    def index_queryset(self):
        return (super(TaxonIndex, self).index_queryset()
                .select_related('family')
                .prefetch_related(
                    'character_values__character',
                    'common_names',
                    'lookalikes',
                    'piles__pilegroup',
                    'synonyms'))

    def prepare(self, obj):
        data = super(TaxonIndex, self).prepare(obj)
        # Boost 150% to help ensure species results come first when
        # searching on scientific names or common names.
        data['boost'] = 1.5
        return data


class FamilyIndex(BaseIndex):
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(use_template=True,
        template_name='simplekey/search_title_family.txt')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_family.txt')

    def index_queryset(self):
        return (super(FamilyIndex, self).index_queryset()
                .prefetch_related('genera'))


class GenusIndex(BaseIndex):
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(use_template=True,
        template_name='simplekey/search_title_genus.txt')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_genus.txt')

    def index_queryset(self):
        return (super(GenusIndex, self).index_queryset()
                .select_related('family')
                .prefetch_related('taxa'))


class PlainPageIndex(BaseIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_plain_page.txt')


class GlossaryTermIndex(BaseIndex):
    name = indexes.CharField(model_attr='term')
    title = indexes.CharField(use_template=True,
        template_name='simplekey/search_title_glossary_term.txt')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_glossary_term.txt')

    def prepare(self, obj):
        data = super(GlossaryTermIndex, self).prepare(obj)
        # Boost glossary results to raise their ranking.
        data['boost'] = 3.0
        return data


class GroupsListPageIndex(BaseIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'simplekey/search_text_groups_list_page.txt')

    def prepare(self, obj):
        data = super(GroupsListPageIndex, self).prepare(obj)
        # Boost helps ensure high ranking when searching on parts of
        # group friendly-names, such as "trees."
        data['boost'] = 8.0
        return data


class SubgroupsListPageIndex(BaseIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'simplekey/search_text_subgroups_list_page.txt')

    def index_queryset(self):
        return (super(SubgroupsListPageIndex, self).index_queryset()
                .select_related('group'))


class SubgroupResultsPageIndex(BaseIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'simplekey/search_text_subgroup_results_page.txt')

    def index_queryset(self):
        return (super(SubgroupResultsPageIndex, self).index_queryset()
                .select_related('subgroup__pilegroup')
                .prefetch_related('subgroup__species__common_names'))


site.register(Taxon, TaxonIndex)
site.register(Family, FamilyIndex)
site.register(Genus, GenusIndex)
site.register(GlossaryTerm, GlossaryTermIndex)
site.register(PlainPage, PlainPageIndex)
site.register(GroupsListPage, GroupsListPageIndex)
site.register(SubgroupsListPage, SubgroupsListPageIndex)
site.register(SubgroupResultsPage, SubgroupResultsPageIndex)
