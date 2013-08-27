from gobotany.core.models import Family, Genus, GlossaryTerm, Taxon
from gobotany.dkey.models import Page
from gobotany.plantshare.models import Question, Sighting
from gobotany.search.models import (GroupsListPage, PlainPage,
    SubgroupsListPage, SubgroupResultsPage)

from haystack import indexes
from haystack import site


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
                            template_name='search_result_url.txt')
    textSpell = indexes.CharField()

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

    def prepare(self, obj):
        """Prepare data for index.

        We make the (spelling) suggestions field mirror the text field,
        but without post-processing.
        (see http://django-haystack.readthedocs.org/en/v1.2.7/installing_search_engines.html#spelling-suggestions)
        """
        prepared_data = super(BaseIndex, self).prepare(obj)
        if 'text' in prepared_data:
            prepared_data['textSpell'] = prepared_data['text']
        return prepared_data


class BaseRealTimeIndex(indexes.RealTimeSearchIndex):
    """ A document that already knows its URL, so searches render faster.
    This is like BaseIndex, but for a RealTimeSearchIndex instead of a
    regular SearchIndex.
    """
    url = indexes.CharField(use_template=True,
                            template_name='search_result_url.txt')

    def read_queryset(self):
        """Bypass `index_queryset()` when we just need to read a model."""
        return self.model._default_manager.all()


# Taxa, Simple-/Full-Key, and Help-section pages

class TaxonIndex(BaseIndex):
    # Index

    name = indexes.CharField(model_attr='scientific_name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='species_text_searchindex.txt')

    # Display

    title = indexes.CharField(use_template=True,
        template_name='species_title_searchindex.txt')

    # Customization

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
    # Index

    name = indexes.CharField(model_attr='name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='family_text_searchindex.txt')

    # Display

    title = indexes.CharField(use_template=True,
        template_name='family_title_searchindex.txt')

    # Customization

    def index_queryset(self):
        return (super(FamilyIndex, self).index_queryset()
                .prefetch_related('genera'))


class GenusIndex(BaseIndex):
    # Index

    name = indexes.CharField(model_attr='name')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='genus_text_searchindex.txt')

    # Display

    title = indexes.CharField(use_template=True,
        template_name='genus_title_searchindex.txt')

    # Customization

    def index_queryset(self):
        return (super(GenusIndex, self).index_queryset()
                .select_related('family')
                .prefetch_related('taxa'))


class PlainPageIndex(BaseIndex):
    # Index

    text = indexes.CharField(
        document=True, use_template=True,
        template_name='plain_page_text_searchindex.txt')

    # Display

    title = indexes.CharField(model_attr='title')


class GlossaryTermIndex(BaseIndex):
    # Index

    name = indexes.CharField(model_attr='term')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='glossary_term_text_searchindex.txt')

    # Display

    title = indexes.CharField(use_template=True,
        template_name='glossary_term_title_searchindex.txt')


class GroupsListPageIndex(BaseIndex):
    # Index

    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'groups_list_page_text_searchindex.txt')

    # Display

    title = indexes.CharField(model_attr='title')

    # Customization

    def prepare(self, obj):
        data = super(GroupsListPageIndex, self).prepare(obj)
        # Boost helps ensure high ranking when searching on parts of
        # group friendly-names, such as "trees."
        data['boost'] = 8.0
        return data


class SubgroupsListPageIndex(BaseIndex):
    # Index

    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'subgroups_list_page_text_searchindex.txt')

    # Display

    title = indexes.CharField(model_attr='title')

    # Customization

    def index_queryset(self):
        return (super(SubgroupsListPageIndex, self).index_queryset()
                .select_related('group'))

    def prepare(self, obj):
        data = super(SubgroupsListPageIndex, self).prepare(obj)
        # Boost helps ensure high ranking when searching on parts of
        # subgroup friendly-names, such as "trees."
        data['boost'] = 4.0
        return data


class SubgroupResultsPageIndex(BaseIndex):
    # Index

    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'subgroup_results_page_text_searchindex.txt')

    # Display

    title = indexes.CharField(model_attr='title')

    # Customization

    def index_queryset(self):
        return (super(SubgroupResultsPageIndex, self).index_queryset()
                .select_related('subgroup__pilegroup')
                .prefetch_related('subgroup__species__common_names'))


# Dichotomous Key pages

class DichotomousKeyPageIndex(BaseIndex):
    # Index

    text = indexes.CharField(
        document=True, use_template=True,
        template_name='dkey_page_text_searchindex.txt')

    # Display

    title = indexes.CharField(use_template=True,
        template_name='dkey_page_title_searchindex.txt')

    # Customization

    def index_queryset(self):
        return (super(DichotomousKeyPageIndex, self).index_queryset()
                .exclude(rank='species')
                .prefetch_related('breadcrumb_cache', 'leads'))

    def prepare(self, obj):
        data = super(DichotomousKeyPageIndex, self).prepare(obj)
        # Boost to help ensure high ranking when searching on family or
        # genus names.
        data['boost'] = 1.2
        return data


# PlantShare pages

class SightingPageIndex(BaseRealTimeIndex):
    # Index

    text = indexes.CharField(
        document=True, use_template=True,
        template_name='sighting_page_text_searchindex.txt')

    # Display

    title = indexes.CharField(use_template=True,
        template_name='sighting_page_title_searchindex.txt')

    # Customization

    def index_queryset(self):
        # Index only publicly shared (and non-rare) plant sightings.
        # (Do not try to show private sightings for the logged-in user here,
        # as it would complicate indexing.)
        return Sighting.objects.public()


class QuestionIndex(BaseRealTimeIndex):
    # Index

    text = indexes.CharField(
        document=True, use_template=True,
        template_name='question_text_searchindex.txt')

    # Display

    title = indexes.CharField(use_template=True,
        template_name='question_title_searchindex.txt')

    # Customization

    def index_queryset(self):
        # Index only published questions, i.e., those with approved answers.
        return Question.objects.answered()


# Register indexes for all desired page/model types.

site.register(Taxon, TaxonIndex)
site.register(Family, FamilyIndex)
site.register(Genus, GenusIndex)
site.register(GlossaryTerm, GlossaryTermIndex)

site.register(PlainPage, PlainPageIndex)
site.register(GroupsListPage, GroupsListPageIndex)
site.register(SubgroupsListPage, SubgroupsListPageIndex)
site.register(SubgroupResultsPage, SubgroupResultsPageIndex)

site.register(Page, DichotomousKeyPageIndex)

site.register(Sighting, SightingPageIndex)
site.register(Question, QuestionIndex)
