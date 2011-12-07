from django.test import TestCase
from django.test.client import Client

from gobotany.simplekey.templatetags.simplekey_extras import italicize_plant

class SimpleTests(TestCase):
    fixtures = ['page_data']

    def test_start_page(self):
        c = Client()
        r = c.get('/1/')
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

