from django.test import TestCase
from django.test.client import Client

from gobotany.core.models import Pile, PileGroup
from gobotany.simplekey.groups_order import ORDERED_GROUPS
from gobotany.simplekey.templatetags.simplekey_extras import italicize_plant
from gobotany.simplekey.views import ordered_pilegroups, ordered_piles

# Following are data for groups and subgroups in the order that they are
# created in the database by the importer. This will be tested against
# the desired display order.

GROUPS = [('Woody Plants', 'woody-plants'),
          ('Aquatic Plants', 'aquatic-plants'),
          ('Graminoids', 'graminoids'),
          ('Monocots', 'monocots'),
          ('Ferns', 'ferns'),
          ('Non-Monocots', 'non-monocots')]

SUBGROUPS = [
    ('woody-plants', 'Woody Angiosperms', 'woody-angiosperms'),
    ('non-monocots', 'Remaining Non-Monocots', 'remaining-non-monocots'),
    ('graminoids', 'Remaining Graminoids', 'remaining-graminoids'),
    ('graminoids', 'Poaceae', 'poaceae'),
    ('non-monocots', 'Composites', 'composites'),
    ('graminoids', 'Carex', 'carex'),
    ('monocots', 'Non-Orchid Monocots', 'non-orchid-monocots'),
    ('woody-plants', 'Woody Gymnosperms', 'woody-gymnosperms'),
    ('ferns', 'Equisetaceae', 'equisetaceae'),
    ('monocots', 'Orchid Monocots', 'orchid-monocots'),
    ('aquatic-plants', 'Thalloid Aquatic', 'thalloid-aquatic'),
    ('ferns', 'Monilophytes', 'monilophytes'),
    ('ferns', 'Lycophytes', 'lycophytes'),
    ('aquatic-plants', 'Non-Thalloid Aquatic', 'non-thalloid-aquatic')
]

def create_groups():
    """Create pile groups and then piles, putting piles into groups in the
    same order that the importer does.
    """
    for name, slug in GROUPS:
        pilegroup = PileGroup(name=name, slug=slug)
        pilegroup.save()
    for pilegroup_slug, name, pile_slug in SUBGROUPS:
        pile = Pile(name=name, slug=pile_slug)
        pile.save()
        pilegroup = PileGroup.objects.get(slug=pilegroup_slug)
        pilegroup.piles.add(pile)
        pilegroup.save()


class SimpleTests(TestCase):

    def setUp(self):
        create_groups()

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
        self.assertEqual(
            [group.keys()[0] for group in ORDERED_GROUPS],
            [pilegroup.slug for pilegroup in ordered_pilegroups()]
        )

    def test_subgroups_count(self):
        self.assertEqual(len(SUBGROUPS), len(Pile.objects.all()))

    def test_subgroups_order(self):
        for group in ORDERED_GROUPS:
            for pilegroup_slug, piles in group.items():
                pilegroup = PileGroup.objects.get(slug=pilegroup_slug)
                self.assertEqual(piles, [pile.slug for pile
                                         in ordered_piles(pilegroup)])

