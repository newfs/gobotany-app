import json

from django.test import TestCase
from django.test.client import Client

from gobotany.core.models import Character, CharacterValue, Pile, PileGroup

from gobotany.simplekey.models import (GroupsListPage,
                                       SearchSuggestion,
                                       SubgroupResultsPage,
                                       SubgroupsListPage)
from gobotany.simplekey.templatetags.simplekey_extras import italicize_plant
from gobotany.simplekey.views import (_format_character_value,
                                      ordered_pilegroups, ordered_piles)

# Following are data for groups and subgroups in the order that they are
# created in the database by the importer. This will be tested against
# the desired display order.

GROUPS = [('Woody Plants', 'woody-plants', 'Woody Plants',
           'Trees, shrubs, sub-shrubs, and lianas'),
          ('Aquatic Plants', 'aquatic-plants', 'Aquatic plants',
           'Plants with most of their parts submerged under water'),
          ('Graminoids', 'graminoids', 'Grass-like plants',
           'Grasses, sedges, and other plants with long, narrow leaves'),
          ('Monocots', 'monocots', 'Orchids and related plants',
           'Lilies, orchids, irises, aroids, and other monocots'),
          ('Ferns', 'ferns', 'Ferns',
           'Ferns, horsetails, quillworts, lycopods, and relatives'),
          ('Non-Monocots', 'non-monocots',
           'All other flowering non-woody plants',
           'Asters and all other flowering dicots')]

SUBGROUPS = [
    ('woody-plants', 'Woody Angiosperms', 'woody-angiosperms',
     'Woody broad-leaved plants', 'Woody broad-leaved plants'),
    ('woody-plants', 'Woody Gymnosperms', 'woody-gymnosperms',
     'Woody needle-leaved plants', 'Woody needle-leaved plants'),
    ('aquatic-plants', 'Non-Thalloid Aquatic', 'non-thalloid-aquatic',
     'Water plants with leaves and stems',
     'Milfoils, watershields, bladderworts, and other submerged plants'),
    ('aquatic-plants', 'Thalloid Aquatic', 'thalloid-aquatic',
     'Tiny water plants with no true stem',
     'Duckweeds and other very small floating species'),
    ('graminoids', 'Carex', 'carex', 'Sedges', 'Plants in the genus Carex'),
    ('graminoids', 'Poaceae', 'poaceae', 'True grasses',
     'Plants in the grass family, Poaceae'),
    ('graminoids', 'Remaining Graminoids', 'remaining-graminoids',
     'All other grass-like plants',
     'Bulrushes, rushes, cat-tails, and other narrow-leaved plants'),
    ('monocots', 'Orchid Monocots', 'orchid-monocots', 'Orchids',
     'Plants in the family Orchidaceae'),
    ('monocots', 'Non-Orchid Monocots', 'non-orchid-monocots',
     'Irises, lilies, and other "monocots"',
     'Lilies, irises, aroids and others'),
    ('ferns', 'Monilophytes', 'monilophytes', 'True ferns and moonworts',
     'Ferns, Moonworts and Adder\'s-tongues with obvious leaves'),
    ('ferns', 'Lycophytes', 'lycophytes',
     'Clubmosses and relatives, plus quillworts',
     'Plants in the families Lycopodiaceae or Isoetaceae'),
    ('ferns', 'Equisetaceae', 'equisetaceae',
     'Horsetails and scouring rushes ',
     'Primitive plants in the genus Equisetum, lacking true leaves'),
    ('non-monocots', 'Composites', 'composites',
     'Daisies, goldenrods, and other aster family plants',
     'Plants in the family Asteraceae'),
    ('non-monocots', 'Remaining Non-Monocots', 'remaining-non-monocots',
     'All other herbaceous, flowering dicots', '')
]

def create_groups():
    """Create pile groups and then piles, putting piles into groups in the
    same order that the importer does.
    """
    for name, slug, friendly_title, friendly_name in GROUPS:
        pilegroup = PileGroup(name=name, slug=slug,
                              friendly_title=friendly_title,
                              friendly_name=friendly_name)
        pilegroup.save()

    for pilegroup_slug, name, pile_slug, friendly_title, friendly_name \
        in SUBGROUPS:

        pile = Pile(name=name, slug=pile_slug, friendly_title=friendly_title,
                    friendly_name=friendly_name)
        pile.save()
        pilegroup = PileGroup.objects.get(slug=pilegroup_slug)
        pilegroup.piles.add(pile)
        pilegroup.save()


def create_simple_key_pages():
    """Create page objects for the Simple Key that supply some basic
    information for page display and for search engine indexing.
    """
    groups_list_page = GroupsListPage(
        title='Simple Key for Plant Identification',
        main_heading='Which group best describes your plant?')
    groups_list_page.save()
    groups_list_page.groups = PileGroup.objects.all()
    groups_list_page.save()

    # Here assume that create_groups() has been called, which creates
    # the PileGroup and Pile records.
    for group in PileGroup.objects.all():
        subgroups_list_page = SubgroupsListPage(
            group=group)
        subgroups_list_page.save()

    for subgroup in Pile.objects.all():
        subgroup_results_page = SubgroupResultsPage(
            subgroup=subgroup)
        subgroup_results_page.save()


class SimpleTests(TestCase):

    def setUp(self):
        create_groups()
        create_simple_key_pages()

    def test_start_page(self):
        c = Client()
        r = c.get('/simple/')
        assert 'Which group best describes your plant?' in r.content


class SimpleKeyExtrasItalicizePlantTestCase(TestCase):
    """Test the 'simplekey_extras' italicize_plant template tag code."""

    # Species

    def test_italicize_plant(self):
        self.assertEqual(
            '<i>Dendrolycopodium</i> <i>dendroideum</i>',
            italicize_plant('Dendrolycopodium dendroideum'))

    def test_italicize_plant_2(self):
        self.assertEqual(
            '<i>Aronia</i> <i>arbutifolia</i>',
            italicize_plant('Aronia arbutifolia'))

    def test_italicize_plant_with_authority(self):
        self.assertEqual(
            '<i>Lycopodium</i> <i>dendroideum</i> Michx.',
            italicize_plant('Lycopodium dendroideum Michx.'))

    def test_italicize_plant_with_authority_2(self):
        self.assertEqual(
            '<i>Aronia</i> <i>pyrifolia</i> Lam.',
            italicize_plant('Aronia pyrifolia Lam.'))

    def test_italicize_plant_with_authority_3(self):
        self.assertEqual(
            '<i>Mespilus</i> <i>arbutifolia</i> L.',
            italicize_plant('Mespilus arbutifolia L.'))

    def test_italicize_plant_with_authority_4(self):
        self.assertEqual(
            '<i>Photinia</i> <i>pyrifolia</i> (Lam.) Robertson & Phipps',
            italicize_plant('Photinia pyrifolia (Lam.) Robertson & Phipps'))

    def test_italicize_plant_with_authority_linneaus_filius(self):
        # L.f. = Linnaeus filius (son of-)
        # from www.environment.gov.au/erin/documentation/pubs/nomenclature.pdf
        self.assertEqual(
            '<i>Pyrus</i> <i>arbutifolia</i> (L.) L. f.',
            italicize_plant('Pyrus arbutifolia (L.) L. f.'))

    # Subspecies

    def test_italicize_plant_subspecies(self):
        self.assertEqual(
            '<i>Solidago</i> <i>speciosa</i> subsp. <i>pallida</i>',
            italicize_plant('Solidago speciosa subsp. pallida'))

    def test_italicize_plant_subspecies_2(self):
        self.assertEqual(
            '<i>Solidago</i> <i>speciosa</i> ssp. <i>pallida</i>',
            italicize_plant('Solidago speciosa ssp. pallida'))

    def test_italicize_plant_subspecies_with_authority(self):
        self.assertEqual(
            ('<i>Cornus</i> <i>alba</i> L. ssp. <i>stolonifera</i> (Michx.) '
             'Wangerin'),
            italicize_plant(
                'Cornus alba L. ssp. stolonifera (Michx.) Wangerin'))

    # Variety

    def test_italicize_plant_variety_with_authority(self):
        self.assertEqual(
            ('<i>Lycopodium</i> <i>obscurum</i> L. var. <i>dendroideum</i> '
             '(Michx.) D.C. Eat.'),
            italicize_plant(
                'Lycopodium obscurum L. var. dendroideum (Michx.) D.C. Eat.'))

    def test_italicize_plant_variety_with_authority_2(self):
        self.assertEqual(
            ('<i>Lycopodium</i> <i>obscurum</i> L. var. <i>hybridum</i> '
             'Farw.'),
            italicize_plant('Lycopodium obscurum L. var. hybridum Farw.'))

    def test_italicize_plant_variety_with_authority_misplaced_period(self):
        self.assertEqual(
            '<i>Aronia.</i> <i>arbutifolia</i> var. <i>glabra</i> Ell.',
            italicize_plant('Aronia. arbutifolia var. glabra Ell.'))

    def test_italicize_plant_variety_with_authority_linnaeus_filius(self):
        self.assertEqual(
            ('<i>Pyrus</i> <i>arbutifolia</i> (L.) L. f. var. <i>glabra</i> '
             'Cronq.'),
            italicize_plant(
                'Pyrus arbutifolia (L.) L. f. var. glabra Cronq.'))

    # Subvariety

    def test_italicize_plant_subvariety_with_authority(self):
        self.assertEqual(
            ('<i>Fritillaria</i> <i>meleagris</i> var. <i>unicolor</i> '
             'subvar. <i>alba</i> AGM'),
            italicize_plant(
                'Fritillaria meleagris var. unicolor subvar. alba AGM'))

    # Form

    def test_italicize_plant_form_with_authority(self):
        self.assertEqual(
            ('<i>Crataegus</i> <i>aestivalis</i> (Walter) Torr. & A.Gray f. '
             '<i>luculenta</i> Sarg.'),
            italicize_plant('Crataegus aestivalis (Walter) Torr. & A.Gray f. '
                            'luculenta Sarg.'))

    # Subform

    def test_italicize_plant_subform(self):
        self.assertEqual(
            '<i>Saxifraga</i> <i>aizoon</i> subf. <i>surculosa</i>',
            italicize_plant('Saxifraga aizoon subf. surculosa'))


    # Names that already have some HTML markup, such as for search
    # results highlighting

    def test_italicize_plant_with_highlight(self):
        self.assertEqual(
            ('<i><span class="highlighted">Aesculus</span></i> <i>glabra</i> '
             '(Ohio buckeye)'),
            italicize_plant('<span class="highlighted">Aesculus</span> '
                            'glabra (Ohio buckeye)'))

    def test_italicize_plant_with_highlight_multiple_words(self):
        # The Haystack highlighter outputs multiple adjacent highlight
        # words as each wrapped with their own span tags.
        self.assertEqual(
            ('<i><span class="highlighted">Aesculus</span></i> '
             '<i><span class="highlighted">glabra</span></i> (Ohio buckeye)'),
            italicize_plant(
                '<span class="highlighted">Aesculus</span> '
                '<span class="highlighted">glabra</span> (Ohio buckeye)'))

    def test_italicize_plant_variety_with_highlight_and_authority(self):
        self.assertEqual(
            ('<i><span class="highlighted">Lycopodium</span></i> '
             '<i><span class="highlighted">obscurum</span></i> '
             'L. var. <i>hybridum</i> Farw.'),
            italicize_plant(
                '<span class="highlighted">Lycopodium</span> '
                '<span class="highlighted">obscurum</span> '
                'L. var. hybridum Farw.'))


class SimpleKeyGroupsOrderTestCase(TestCase):
    """Test the display order of plant groups and subgroups."""

    def setUp(self):
        create_groups()

    def test_groups_count(self):
        self.assertEqual(len(GROUPS), len(PileGroup.objects.all()))

    def test_groups_order(self):
        grouplist = ordered_pilegroups()
        self.assertEqual(grouplist[0].slug, 'woody-plants')
        self.assertEqual(grouplist[-1].slug, 'non-monocots')

    def test_subgroups_count(self):
        self.assertEqual(len(SUBGROUPS), len(Pile.objects.all()))

    def test_subgroups_order(self):
        pilegroup = PileGroup.objects.filter(slug='graminoids').all()[0]
        pilelist = ordered_piles(pilegroup)
        self.assertEqual(len(pilelist), 3)
        self.assertEqual(pilelist[0].slug, 'carex')
        self.assertEqual(pilelist[1].slug, 'poaceae')
        self.assertEqual(pilelist[2].slug, 'remaining-graminoids')

class SearchSuggestionsTestCase(TestCase):
    """General tests for the search suggestions Web service API."""

    def create_search_suggestions(self):
        # Include a case-sensitive repeat suggestion ("ferns") just
        # for testing, even though this might be eliminated in the
        # import routines.
        SUGGESTIONS = ['fern flatsedge', 'fern-leaved yarrow', 'Ferns',
                       'fern-leaved false foxglove', 'ferns', 'fern',
                       'fern grass']
        for suggestion in SUGGESTIONS:
            s, created = SearchSuggestion.objects.get_or_create(
                term=suggestion)

    def setUp(self):
        self.create_search_suggestions()

    def test_search_suggestions_have_no_duplicates(self):
        # The search suggestions are meant to be case-insensitive in the
        # user interface, but the database field is case-sensitive.
        # Ensure that the search suggestions do not include any duplicates
        # that may exist in the database due to case sensitivity.
        EXPECTED_SUGGESTIONS = ['fern flatsedge', 'fern-leaved yarrow',
                                'fern-leaved false foxglove', 'ferns',
                                'fern', 'fern grass']
        client = Client()
        response = client.get('/suggest/?q=fer')
        #print 'response.content:', response.content
        suggestions = json.loads(response.content)
        self.assertEqual(sorted(suggestions), sorted(EXPECTED_SUGGESTIONS))


class SimpleKeyPagesSearchSuggestionsTestCase(TestCase):
    """Test the search suggestions generated for each Simple Key page
    that are to be added to the database by the importer.
    """

    def setUp(self):
        create_groups()
        create_simple_key_pages()

    # Simple Key feature

    def test_groups_list_page_suggestions(self):
        EXPECTED_SUGGESTIONS = ['simple key', 'plant identification']
        groups_list_page = GroupsListPage.objects.all()[0]
        self.assertEqual(sorted(groups_list_page.search_suggestions()),
                         sorted(EXPECTED_SUGGESTIONS))

    # Plant groups

    def _subgroups_list_suggestions(self, group_name):
        subgroups_list_page = SubgroupsListPage.objects.get(
            group__name=group_name)
        suggestions = subgroups_list_page.search_suggestions()
        return suggestions

    def test_subgroups_list_page_woody_plants_suggestions(self):
        EXPECTED_SUGGESTIONS = ['woody plants', 'trees', 'shrubs',
                                'sub-shrubs', 'lianas']
        self.assertEqual(
            sorted(self._subgroups_list_suggestions('Woody Plants')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroups_list_page_aquatic_plants_suggestions(self):
        EXPECTED_SUGGESTIONS = ['aquatic plants']
        self.assertEqual(
            sorted(self._subgroups_list_suggestions('Aquatic Plants')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroups_list_page_grasses_suggestions(self):
        EXPECTED_SUGGESTIONS = ['grass-like plants', 'grasses', 'sedges',
                                'narrow leaves']
        self.assertEqual(
            sorted(self._subgroups_list_suggestions('Graminoids')),
            sorted(EXPECTED_SUGGESTIONS))


    def test_subgroups_list_page_orchids_suggestions(self):
        EXPECTED_SUGGESTIONS = ['orchids', 'lilies', 'irises', 'aroids',
                                'monocots']
        self.assertEqual(
            sorted(self._subgroups_list_suggestions('Monocots')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroups_list_page_ferns_suggestions(self):
        EXPECTED_SUGGESTIONS = ['ferns', 'horsetails', 'quillworts',
                                'lycopods']
        self.assertEqual(
            sorted(self._subgroups_list_suggestions('Ferns')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroups_list_page_non_monocots_suggestions(self):
        EXPECTED_SUGGESTIONS = ['asters', 'flowering dicots']
        self.assertEqual(
            sorted(self._subgroups_list_suggestions('Non-Monocots')),
            sorted(EXPECTED_SUGGESTIONS))

    # Plant subgroups

    def _subgroup_results_suggestions(self, subgroup_name):
        subgroup_results_page = SubgroupResultsPage.objects.get(
            subgroup__name=subgroup_name)
        suggestions = subgroup_results_page.search_suggestions()
        return suggestions

    def test_subgroup_results_page_angiosperms_suggestions(self):
        EXPECTED_SUGGESTIONS = ['woody broad-leaved plants']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Woody Angiosperms')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_gymnosperms_suggestions(self):
        EXPECTED_SUGGESTIONS = ['woody needle-leaved plants']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Woody Gymnosperms')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_non_thalloid_aquatic_suggestions(self):
        EXPECTED_SUGGESTIONS = ['water plants', 'milfoils', 'watershields',
                                'bladderworts', 'submerged plants']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions(
                   'Non-Thalloid Aquatic')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_thalloid_aquatic_suggestions(self):
        EXPECTED_SUGGESTIONS = ['duckweeds', 'tiny water plants']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Thalloid Aquatic')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_carex_suggestions(self):
        EXPECTED_SUGGESTIONS = ['sedges']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Carex')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_poaceae_suggestions(self):
        EXPECTED_SUGGESTIONS = ['poaceae', 'true grasses']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Poaceae')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_remaining_graminoids_suggestions(self):
        EXPECTED_SUGGESTIONS = ['grass-like plants', 'bulrushes', 'rushes',
                                'cat-tails', 'narrow-leaved plants']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions(
                   'Remaining Graminoids')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_orchid_monocots_suggestions(self):
        EXPECTED_SUGGESTIONS = ['orchids']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Orchid Monocots')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_non_orchid_monocots_suggestions(self):
        EXPECTED_SUGGESTIONS = ['irises', 'lilies', 'aroids', 'monocots']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Non-Orchid Monocots')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_monilophytes_suggestions(self):
        EXPECTED_SUGGESTIONS = ['true ferns', 'ferns', 'moonworts',
                                'adder\'s-tongues']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Monilophytes')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_lycophytes_suggestions(self):
        EXPECTED_SUGGESTIONS = ['clubmosses', 'quillworts']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Lycophytes')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_equisetaceae_suggestions(self):
        EXPECTED_SUGGESTIONS = ['horsetails', 'scouring rushes']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Equisetaceae')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_composites_suggestions(self):
        EXPECTED_SUGGESTIONS = ['aster family plants', 'daisies',
                                'goldenrods']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions('Composites')),
            sorted(EXPECTED_SUGGESTIONS))

    def test_subgroup_results_page_remaining_non_monocots_suggestions(self):
        EXPECTED_SUGGESTIONS = ['flowering dicots']
        self.assertEqual(
            sorted(self._subgroup_results_suggestions(
                   'Remaining Non-Monocots')),
            sorted(EXPECTED_SUGGESTIONS))


class FormatCharacterValueTestCase(TestCase):
    """Tests for character value display formatting."""

    def _assert_unicode_equal(self, expected_value, actual_value):
        # Use repr() to avoid the error "unprintable AssertionError object"
        # when the values are not equal.
        self.assertEqual(repr(expected_value), repr(actual_value))

    def test_character_value_displays_numeric_range(self):
        character = Character(short_name='leaf_blade_length_ap',
                              name='Leaf blade length',
                              friendly_name='Leaf blade length',
                              character_group_id=0,
                              value_type='LENGTH',
                              unit='cm')
        character.save()
        character_value = CharacterValue(character=character,
                                         value_min=200.0,
                                         value_max=2500.0)
        character_value.save()

        expected_value = u'200\u20132500 cm'
        actual_value = _format_character_value(character_value)
        self._assert_unicode_equal(expected_value, actual_value)

    def test_character_value_collapses_range_when_min_equals_max(self):
        character = Character(short_name='sepal_number_ap',
                              name='Sepal number',
                              friendly_name='Sepal number',
                              character_group_id=0,
                              value_type='LENGTH',
                              unit='NA')
        character.save()
        character_value = CharacterValue(character=character,
                                         value_min=2.0,
                                         value_max=2.0)
        character_value.save()

        expected_value = u'2'
        actual_value = _format_character_value(character_value)
        self._assert_unicode_equal(expected_value, actual_value)
