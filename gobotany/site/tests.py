"""Tests of whether our basic site layout is present."""

from datetime import datetime
from gobotany.libtest import FunctionalCase

class FunctionalTests(FunctionalCase):

    def test_home_page(self):
        self.get('/')

        title = self.css1('title').text
        self.assertEqual(title, 'Go Botany: New England Wild Flower Society')

        get_started = self.css1('#cta')
        self.assertEqual(get_started.get('href'), '/simple/')
        self.assertEqual(get_started.text, 'Get Started')

    def test_groups_page(self):
        self.get('/simple/')

        h3 = self.css('h3')
        self.assertEqual(len(h3), 6)
        assert h3[0].text.startswith('Woody plants')
        assert h3[1].text.startswith('Aquatic plants')
        assert h3[2].text.startswith('Grass-like plants')
        assert h3[3].text.startswith('Orchids and related plants')
        assert h3[4].text.startswith('Ferns')
        assert h3[5].text.startswith('All other flowering non-woody plants')

        # Do group links get constructed correctly?

        e = self.css1('.plant-in-group')
        self.assertEqual('My plant is in this group', e.text)
        self.assertEqual(e.get('href'), '/simple/woody-plants/')

    def test_subgroups_page(self):
        self.get('/simple/ferns/')
        q = self.css('h3')
        self.assertEqual(len(q), 3)
        assert q[0].text.startswith('True ferns and moonworts')
        assert q[1].text.startswith('Clubmosses and relatives, plus quillworts')
        assert q[2].text.startswith('Horsetails and scouring-rushes')
        q = self.css('.plant-in-subgroup')
        self.assertTrue(q[0].get('href').endswith('/ferns/monilophytes/'))
        self.assertTrue(q[1].get('href').endswith('/ferns/lycophytes/'))
        self.assertTrue(q[2].get('href').endswith('/ferns/equisetaceae/'))

    def test_copyright_contains_current_year(self):
        self.get('/')
        copyright = self.css1('footer .copyright')
        current_year = str(datetime.now().year)
        self.assertIn(current_year, copyright.text)
