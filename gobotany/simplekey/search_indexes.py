from haystack import indexes
from haystack import site

from gobotany.core.models import Taxon, Family, Genus

from gobotany.simplekey.models import (HelpPage, GlossaryHelpPage,
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


class TaxonIndex(indexes.SearchIndex):
    scientific_name = indexes.CharField(model_attr='scientific_name')
    title = indexes.CharField(use_template=True,
        template_name='simplekey/search_title_species.txt')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_species.txt')

    def index_queryset(self):
        return Taxon.objects.filter()

    def prepare(self, obj):
        data = super(TaxonIndex, self).prepare(obj)
        # Boost 150% to help ensure species results come first when
        # searching on scientific names or common names.
        data['boost'] = 1.5
        return data


class FamilyIndex(indexes.SearchIndex):
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(use_template=True,
        template_name='simplekey/search_title_family.txt')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_family.txt')


class GenusIndex(indexes.SearchIndex):
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(use_template=True,
        template_name='simplekey/search_title_genus.txt')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_genus.txt')


class HelpPageIndex(indexes.SearchIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_help_page.txt')


class GlossaryHelpPageIndex(indexes.SearchIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='simplekey/search_text_glossary_help_page.txt')

    def prepare(self, obj):
        data = super(GlossaryHelpPageIndex, self).prepare(obj)
        # Boost glossary pages 200% to help ensure they come first when
        # searching on glossary terms.
        data['boost'] = 2.0
        return data


class GroupsListPageIndex(indexes.SearchIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'simplekey/search_text_groups_list_page.txt')

    def prepare(self, obj):
        data = super(GroupsListPageIndex, self).prepare(obj)
        # Boost 200% to help ensure high ranking when searching on
        # parts of group friendly names, such as "trees."
        data['boost'] = 2.0
        return data


class SubgroupsListPageIndex(indexes.SearchIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'simplekey/search_text_subgroups_list_page.txt')


class SubgroupResultsPageIndex(indexes.SearchIndex):
    title = indexes.CharField(model_attr='title')
    text = indexes.CharField(
        document=True, use_template=True,
        template_name = 'simplekey/search_text_subgroup_results_page.txt')


site.register(Taxon, TaxonIndex)
site.register(Family, FamilyIndex)
site.register(Genus, GenusIndex)
site.register(HelpPage, HelpPageIndex)
site.register(GlossaryHelpPage, GlossaryHelpPageIndex)
site.register(GroupsListPage, GroupsListPageIndex)
site.register(SubgroupsListPage, SubgroupsListPageIndex)
site.register(SubgroupResultsPage, SubgroupResultsPageIndex)
