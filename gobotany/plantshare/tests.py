"""Basic PlantShare functional tests that do not require a browser."""

from gobotany.libtest import FunctionalCase

class PlantShareTests(FunctionalCase):

    def _get_plantshare(self, url_path):
        PLANTSHARE_BASE = '/ps'
        self.get(PLANTSHARE_BASE + url_path)

    # PlantShare main page

    MAIN_URL = '/'

    def test_main_page_title(self):
        self._get_plantshare(self.MAIN_URL)
        title = self.css1('title').text
        self.assertEqual(title, 'PlantShare: Go Botany')

    def test_main_page_main_heading(self):
        self._get_plantshare(self.MAIN_URL)
        h1 = self.css1('h1').text
        self.assertEqual(h1, 'PlantShare')

    def test_main_page_has_signup_nav_link(self):
        self._get_plantshare(self.MAIN_URL)
        self.assertIsNotNone(self.link_saying('Sign Up for PlantShare'))

    def test_main_page_has_signup_call_to_action(self):
        self._get_plantshare(self.MAIN_URL)
        self.assertTrue(self.css1('.sign-up-call'))

    def test_main_page_has_login_form(self):
        self._get_plantshare(self.MAIN_URL)
        self.assertTrue(self.css1('#login.box'))

    # Sign Up for PlantShare page

    SIGNUP_FORM_URL = '/accounts/register/'

    def test_signup_page_title(self):
        self._get_plantshare(self.SIGNUP_FORM_URL)
        title = self.css1('title').text
        self.assertEqual(title, 'Sign Up for PlantShare: Go Botany')

    def test_signup_page_main_heading(self):
        self._get_plantshare(self.SIGNUP_FORM_URL)
        h1 = self.css1('h1').text
        self.assertEqual(h1, 'Sign Up for PlantShare')

    def test_signup_page_has_plantshare_nav_link(self):
        self._get_plantshare(self.SIGNUP_FORM_URL)
        self.assertIsNotNone(self.link_saying('PlantShare'))
