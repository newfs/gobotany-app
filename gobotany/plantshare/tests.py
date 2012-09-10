from gobotany.libtest import FunctionalCase

class PlantShareTests(FunctionalCase):

    def _get_plantshare(self, url_path):
        PLANTSHARE_BASE = '/ps'
        self.get(PLANTSHARE_BASE + url_path)

    def test_main_plantshare_page(self):
        self._get_plantshare('/')
        title = self.css1('title').text
        self.assertEqual(title, 'PlantShare: Go Botany')
        h1 = self.css1('h1').text
        self.assertEqual(h1, 'PlantShare')

    def test_signup_page(self):
        self._get_plantshare('/accounts/register/')
        title = self.css1('title').text
        self.assertEqual(title, 'Sign Up for PlantShare: Go Botany')
        h1 = self.css1('h1').text
        self.assertEqual(h1, 'Sign Up for PlantShare')
