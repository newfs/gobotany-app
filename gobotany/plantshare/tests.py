"""Basic PlantShare functional tests that do not require a browser."""

import json
import os
import unittest

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.test.client import Client

from lxml import etree
from lxml.cssselect import CSSSelector

from selenium.common.exceptions import NoSuchElementException

from gobotany.core.models import (ConservationStatus, CommonName, Family,
    Genus, Synonym, Taxon)
from gobotany.plantshare.models import Location


TEST_USERNAME = 'test'
TEST_EMAIL = 'test@test.com'
TEST_PASSWORD = 'testpass'

def _setup_sample_data():
    group, created = Group.objects.get_or_create(
        name=settings.AGREED_TO_TERMS_GROUP)
    user = User.objects.create_user(TEST_USERNAME, TEST_EMAIL,
        TEST_PASSWORD)
    # Add the test user to the "agreed to terms" group, so tests can
    # run as if the user already accepted the PlantShare Terms.
    group.user_set.add(user)

class PlantShareTests(TestCase):
    PLANTSHARE_BASE = '/plantshare'

    @classmethod
    def setUpTestData(cls):
        _setup_sample_data()
        cls.client = Client()

    def css(self, response, selector):
        if response.status_code == 200:
            content = response.content
            if content.startswith(b'<?xml'):
                self.tree = etree.fromstring(content)
            else:
                parser = etree.HTMLParser()
                self.tree = etree.fromstring(content, parser)

        lxml_elements = CSSSelector(selector)(self.tree)
        return [ element for element in lxml_elements ]

    def _get_plantshare(self, url_path, log_in=False, username=TEST_USERNAME,
            password=TEST_PASSWORD):
        """Get a PlantShare page."""
        url = self.PLANTSHARE_BASE + url_path
        client = None
        if log_in:
            client = Client()
            client.login(username=username, password=password)
            self.client = client
        response = self.client.get(url)
        return response

    # Test helpers

    def _page_title(self, url_path, log_in=False):
        """Return the HTML title for a page."""
        response = self._get_plantshare(url_path, log_in=log_in)
        title = self.css(response, 'title')
        title_text = str(etree.tostring(title[0]))
        return title_text

    def _page_heading(self, url_path, log_in=False):
        """Return the main (h1) heading for a page."""
        response = self._get_plantshare(url_path, log_in=log_in)
        heading = self.css(response, 'h1')
        heading_text = str(etree.tostring(heading[0]))
        return heading_text

    ### TESTS ###

    # PlantShare main page

    MAIN_URL = '/'

    def test_main_page_title(self):
        page_title = self._page_title(self.MAIN_URL)
        self.assertTrue(page_title.find('PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_main_page_main_heading(self):
        page_heading = self._page_heading(self.MAIN_URL)
        self.assertTrue(page_heading.find('PlantShare') > -1)

    # PlantShare main page: when user is logged out

    def test_main_page_logged_out_has_signup_nav_link(self):
        response = self._get_plantshare(self.MAIN_URL)
        signup_link = self.css(response, 'nav .signup a')
        signup_link_text = str(etree.tostring(signup_link[0]))
        self.assertTrue(signup_link_text.find(
            'Sign Up for PlantShare') > -1)

    def test_main_page_logged_out_has_signup_call_to_action(self):
        response = self._get_plantshare(self.MAIN_URL)
        signup_heading = self.css(response, '.sign-up-call h2')
        signup_heading_text = str(etree.tostring(signup_heading[0]))
        self.assertTrue(signup_heading_text.find(
            'Sign up for PlantShare') > -1)

    def test_main_page_logged_out_has_login_form(self):
        response = self._get_plantshare(self.MAIN_URL)
        self.assertTrue(self.css(response, '#login.box'))

    def test_main_page_logged_out_omits_profile_box(self):
        response = self._get_plantshare(self.MAIN_URL)
        self.assertFalse(self.css(response, '.profile.box'))

    def test_main_page_logged_out_omits_profile_nav_link(self):
        response = self._get_plantshare(self.MAIN_URL)
        self.assertFalse(self.css(response, 'nav .profile a'))

    def test_main_page_logged_out_omits_logout_link(self):
        response = self._get_plantshare(self.MAIN_URL)
        self.assertFalse(self.css(response, 'nav .logout a'))

    # PlantShare main page: when user is logged in

    def test_main_page_logged_in_has_profile_box(self):
        response = self._get_plantshare(self.MAIN_URL, log_in=True)
        profile_heading = self.css(response, '.profile.box h2')
        profile_heading_text = str(etree.tostring(profile_heading[0]))
        self.assertTrue(profile_heading_text.find('Your Profile') > -1)

    def test_main_page_logged_in_has_profile_nav_item(self):
        response = self._get_plantshare(self.MAIN_URL, log_in=True)
        profile_link = self.css(response, 'nav .profile a')
        profile_link_text = str(etree.tostring(profile_link[0]))
        self.assertTrue(profile_link_text.find('Your Profile') > -1)

    def test_main_page_logged_in_has_logout_nav_item(self):
        response = self._get_plantshare(self.MAIN_URL, log_in=True)
        logout_link = self.css(response, 'nav .logout a')
        logout_link_text = str(etree.tostring(logout_link[0]))
        self.assertTrue(logout_link_text.find(
            'Log Out ' + TEST_USERNAME) > -1)

    def test_main_page_logged_in_omits_signup_nav_item(self):
        response = self._get_plantshare(self.MAIN_URL, log_in=True)
        decoded_html = response.content.decode('utf-8')
        self.assertTrue(decoded_html.find('Sign Up For Plantshare') == -1)

    def test_main_page_logged_in_omits_signup_call_to_action(self):
        response = self._get_plantshare(self.MAIN_URL, log_in=True)
        self.assertFalse(self.css(response, '.sign-up-call'))

    def test_main_page_logged_in_omits_login_form(self):
        response = self._get_plantshare(self.MAIN_URL, log_in=True)
        self.assertFalse(self.css(response, '#login.box'))

    # Log In page: used only for login errors or when users attempt to
    # visit a URL that requires login. The usual place to log in is the
    # form in the sidebthe PlantShare main page.

    LOG_IN_URL = '/accounts/login/'

    def test_login_page_title(self):
        page_title = self._page_title(self.LOG_IN_URL)
        self.assertTrue(page_title.find('Log In: PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_login_page_main_heading(self):
        page_heading = self._page_heading(self.LOG_IN_URL)
        self.assertTrue(page_heading.find('Log In') > -1)

    def test_login_page_has_plantshare_nav_link(self):
        response = self._get_plantshare(self.LOG_IN_URL, log_in=True)
        link = self.css(response, 'nav .plantshare a')
        link_text = str(etree.tostring(link[0]))
        self.assertTrue(link_text.find('PlantShare') > -1)

    def test_login_page_has_minimal_navigation(self):
        response = self._get_plantshare(self.LOG_IN_URL)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertEqual(len(navigation_items), 1)

    def test_login_page_has_message_requesting_login_to_continue(self):
        # Get a page requiring login.
        response = self._get_plantshare(
            '/accounts/login/?next=/plantshare/profile/')
        message = self.css(response, 'h1 + p')
        message_text = str(etree.tostring(message[0]))
        self.assertTrue(message_text.find('Please log in to continue.') > -1)

    def test_login_page_occurs_upon_bad_login(self):
        response = self._get_plantshare(
            '/accounts/login/?next=/plantshare/profile/', log_in=True,
            username='nobody', password='nothing')
        heading = self.css(response, 'h1')
        heading_text = str(etree.tostring(heading[0]))
        self.assertTrue(heading_text.find('Log In') > -1)

    # Log Out confirmation page

    LOG_OUT_URL = '/accounts/logout/'

    def test_log_out_page_title(self):
        page_title = self._page_title(self.LOG_OUT_URL)
        self.assertTrue(page_title.find('Logged Out: PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_log_out_page_main_heading(self):
        page_heading = self._page_heading(self.LOG_OUT_URL)
        self.assertTrue(page_heading.find('Logged Out') > -1)

    def test_log_out_page_has_plantshare_nav_item(self):
        response = self._get_plantshare(self.LOG_OUT_URL)
        plantshare_link = self.css(response, 'nav .plantshare a')
        plantshare_link_text = str(etree.tostring(plantshare_link[0]))
        self.assertTrue(plantshare_link_text.find('PlantShare') > -1)

    def test_log_out_page_has_basic_navigation(self):
        # The Logged Out page should show the basic PlantShare
        # navigation elements that appear when a user is logged out.
        response = self._get_plantshare(self.LOG_OUT_URL)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertEqual(len(navigation_items), 5)

    # Sign Up for PlantShare page

    SIGNUP_FORM_URL = '/accounts/register/'

    def test_signup_page_title(self):
        page_title = self._page_title(self.SIGNUP_FORM_URL)
        self.assertTrue(page_title.find('Sign Up for PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_signup_page_main_heading(self):
        page_heading = self._page_heading(self.SIGNUP_FORM_URL)
        self.assertTrue(page_heading.find('Sign Up for PlantShare') > -1)

    def test_signup_page_has_plantshare_nav_item(self):
        response = self._get_plantshare(self.SIGNUP_FORM_URL)
        plantshare_link = self.css(response, 'nav .plantshare a')
        plantshare_link_text = str(etree.tostring(plantshare_link[0]))
        self.assertTrue(plantshare_link_text.find('PlantShare') > -1)

    def test_signup_page_has_minimal_navigation(self):
        response = self._get_plantshare(self.SIGNUP_FORM_URL)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertEqual(len(navigation_items), 2)   # includes Signup item

    # Ensure that the replacement for ReCaptcha—a visually-hidden URL field
    # that should be empty—fails with an error if it has any text.
    def test_sign_up_with_text_in_hidden_url_field_fails(self):
        form_submit_url = self.PLANTSHARE_BASE + self.SIGNUP_FORM_URL
        client = Client()
        response = client.post(form_submit_url, {'username': 'test2',
            'email': 'test2@test2.net', 'password1': 'testpass2',
            'password2': 'testpass2', 'url': 'asdf'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'The URL field should be blank.' in response.content)

    # Registration Complete page (next step: activate from email)

    REG_COMPLETE_URL = '/accounts/register/complete/'

    def test_registration_complete_page_title(self):
        page_title = self._page_title(self.REG_COMPLETE_URL)
        self.assertTrue(page_title.find('Sign Up Complete: PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_registration_complete_page_main_heading(self):
        page_heading = self._page_heading(self.REG_COMPLETE_URL)
        self.assertTrue(page_heading.find('Sign Up Complete') > -1)

    def test_registration_complete_page_has_plantshare_nav_item(self):
        response = self._get_plantshare(self.REG_COMPLETE_URL)
        plantshare_link = self.css(response, 'nav .plantshare a')
        plantshare_link_text = str(etree.tostring(plantshare_link[0]))
        self.assertTrue(plantshare_link_text.find('PlantShare') > -1)

    def test_registration_complete_page_has_minimal_navigation(self):
        response = self._get_plantshare(self.REG_COMPLETE_URL)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertEqual(len(navigation_items), 1)

    # Activation Complete page

    ACTIVATION_COMPLETE_URL = '/accounts/activate/complete/'

    def test_activation_complete_page_title(self):
        page_title = self._page_title(self.ACTIVATION_COMPLETE_URL)
        self.assertTrue(page_title.find('Activation Complete: PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_activation_complete_page_main_heading(self):
        page_heading = self._page_heading(self.ACTIVATION_COMPLETE_URL)
        self.assertTrue(page_heading.find('Activation Complete') > -1)

    def test_activation_complete_page_has_plantshare_nav_item(self):
        response = self._get_plantshare(self.ACTIVATION_COMPLETE_URL)
        plantshare_link = self.css(response, 'nav .plantshare a')
        plantshare_link_text = str(etree.tostring(plantshare_link[0]))
        self.assertTrue(plantshare_link_text.find('PlantShare') > -1)

    def test_activation_complete_page_has_minimal_navigation(self):
        response = self._get_plantshare(self.ACTIVATION_COMPLETE_URL)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertEqual(len(navigation_items), 1)

    # Post a (new) Sighting form page

    NEW_SIGHTING_URL = '/sightings/new/'

    def test_new_sighting_form_page_requires_login(self):
        response = self._get_plantshare(
            '/accounts/login/?next=/plantshare/sightings/new/', log_in=False)
        heading = self.css(response, 'h1')
        heading_text = str(etree.tostring(heading[0]))
        self.assertTrue(heading_text.find('Log In') > -1)

    def test_new_sighting_form_page_title(self):
        page_title = self._page_title(self.NEW_SIGHTING_URL, log_in=True)
        self.assertTrue(page_title.find('Post a Sighting: PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_new_sighting_form_page_main_heading(self):
        page_heading = self._page_heading(self.NEW_SIGHTING_URL, log_in=True)
        self.assertTrue(page_heading.find('Post a Sighting') > -1)

    def test_new_sighting_form_page_has_plantshare_nav_item(self):
        response = self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        plantshare_link = self.css(response, 'nav .plantshare a')
        plantshare_link_text = str(etree.tostring(plantshare_link[0]))
        self.assertTrue(plantshare_link_text.find('PlantShare') > -1)

    def test_new_sighting_form_page_has_post_a_sighting_nav_item(self):
        response = self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        nav_item = self.css(response, 'nav .post-sighting a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('Post a Sighting') > -1)

    def test_new_sighting_form_page_has_profile_nav_item(self):
        response = self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        nav_item = self.css(response, 'nav .profile a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('Your Profile') > -1)

    def test_new_sighting_form_page_has_full_navigation(self):
        response = self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertTrue(len(navigation_items) > 1)

    # Post a (new) Sighting: "done" page

    NEW_SIGHTING_DONE_URL = '/sightings/new/done/'

    def test_new_sighting_done_page_requires_login(self):
        response = self._get_plantshare(
            '/accounts/login/?next=/plantshare/sightings/new/done/',
            log_in=False)
        heading = self.css(response, 'h1')
        heading_text = str(etree.tostring(heading[0]))
        self.assertTrue(heading_text.find('Log In') > 1)

    def test_new_sighting_done_page_title(self):
        page_title = self._page_title(self.NEW_SIGHTING_DONE_URL, log_in=True)
        self.assertTrue(page_title.find('Sighting Posted: PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_new_sighting_done_page_main_heading(self):
        page_heading = self._page_heading(self.NEW_SIGHTING_DONE_URL,
            log_in=True)
        self.assertTrue(page_heading.find('Sighting Posted') > -1)

    def test_new_sighting_done_page_has_plantshare_nav_item(self):
        response = self._get_plantshare(self.NEW_SIGHTING_DONE_URL,
            log_in=True)
        nav_item = self.css(response, 'nav .plantshare a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('PlantShare') > -1)

    def test_new_sighting_done_page_has_post_a_sighting_nav_item(self):
        response = self._get_plantshare(self.NEW_SIGHTING_DONE_URL,
            log_in=True)
        nav_item = self.css(response, 'nav .post-sighting a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('Post a Sighting') > -1)

    def test_new_sighting_done_page_has_profile_nav_item(self):
        response = self._get_plantshare(self.NEW_SIGHTING_DONE_URL,
            log_in=True)
        nav_item = self.css(response, 'nav .profile a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('Your Profile') > -1)

    def test_new_sighting_done_page_has_full_navigation(self):
        response = self._get_plantshare(self.NEW_SIGHTING_DONE_URL,
            log_in=True)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertTrue(len(navigation_items) > 1)

    # Your Profile page

    YOUR_PROFILE_URL = '/profile/'

    def test_profile_page_requires_login(self):
        response = self._get_plantshare(
            '/accounts/login/?next=/plantshare/profile/', log_in=False)
        heading = self.css(response, 'h1')
        heading_text = str(etree.tostring(heading[0]))
        self.assertTrue(heading_text.find('Log In') > 1)

    def test_profile_page_title(self):
        page_title = self._page_title(self.YOUR_PROFILE_URL, log_in=True)
        self.assertTrue(page_title.find('Your Profile: PlantShare:') > -1)
        self.assertTrue(page_title.find('Go Botany') > -1)

    def test_profile_page_main_heading(self):
        page_heading = self._page_heading(self.YOUR_PROFILE_URL, log_in=True)
        self.assertTrue(page_heading.find('Your Profile') > -1)

    def test_profile_page_has_plantshare_nav_item(self):
        response = self._get_plantshare(self.YOUR_PROFILE_URL, log_in=True)
        nav_item = self.css(response, 'nav .plantshare a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('PlantShare') > -1)

    def test_profile_page_has_post_a_sighting_nav_item(self):
        response = self._get_plantshare(self.YOUR_PROFILE_URL, log_in=True)
        nav_item = self.css(response, 'nav .post-sighting a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('Post a Sighting') > -1)

    def test_profile_page_has_profile_nav_item(self):
        response = self._get_plantshare(self.YOUR_PROFILE_URL, log_in=True)
        nav_item = self.css(response, 'nav .profile a')
        nav_item_text = str(etree.tostring(nav_item[0]))
        self.assertTrue(nav_item_text.find('Your Profile') > -1)

    def test_profile_page_has_full_navigation(self):
        response = self._get_plantshare(self.YOUR_PROFILE_URL, log_in=True)
        navigation_items = self.css(response, '#sidebar nav li')
        self.assertTrue(len(navigation_items) > 1)









class LocationModelTests(TestCase):

    def test_location_save_parses_input_city_state(self):
        location = Location(user_input='Framingham, MA')
        location.save()
        self.assertEqual(location.city, 'Framingham')
        self.assertEqual(location.state, 'MA')

    def test_location_save_parses_input_address_city_state(self):
        location = Location(user_input='180 Hemenway Road, Framingham, MA')
        location.save()
        self.assertEqual(location.street, '180 Hemenway Road')
        self.assertEqual(location.city, 'Framingham')
        self.assertEqual(location.state, 'MA')

    def test_location_save_parses_input_ignores_lat_long_numeric(self):
        location = Location(user_input='41.2342, -76.2928')
        location.save()
        # Because latitude and longitude are now parsed and geocoded
        # from the client during form input instead, doing a save on the
        # location model does not populate the individual fields.
        self.assertEqual(location.latitude, None)
        self.assertEqual(location.longitude, None)

    def test_location_save_parses_input_ignores_garbage_letters(self):
        location = Location(user_input='enutharocegusahosecsahkm')
        location.save()
        self.assertIsNone(location.street)
        self.assertIsNone(location.city)
        self.assertIsNone(location.state)
        self.assertIsNone(location.postal_code)
        self.assertIsNone(location.latitude)
        self.assertIsNone(location.longitude)

    def test_location_save_parses_input_ignores_garbage_numbers(self):
        location = Location(user_input='12873498712983749182')
        location.save()
        self.assertIsNone(location.street)
        self.assertIsNone(location.city)
        self.assertIsNone(location.state)
        self.assertIsNone(location.postal_code)
        self.assertIsNone(location.latitude)
        self.assertIsNone(location.longitude)

    def test_location_save_parses_input_ignores_garbage_mixed(self):
        location = Location(user_input='aoeua87aoe349a8712b8qjk37a')
        location.save()
        self.assertIsNone(location.street)
        self.assertIsNone(location.city)
        self.assertIsNone(location.state)
        self.assertIsNone(location.postal_code)
        self.assertIsNone(location.latitude)
        self.assertIsNone(location.longitude)


class SightingsRestrictionsTests(TestCase):

    URL_BASE = '/plantshare/api/restrictions/?'

    TEST_USERNAME = 'test'
    TEST_EMAIL = 'test@test.com'
    TEST_PASSWORD = 'testpass'

    def setUp(self):
        self.group, created = Group.objects.get_or_create(
            name=settings.AGREED_TO_TERMS_GROUP)

        self.user = User.objects.create_user(
            self.TEST_USERNAME, self.TEST_EMAIL, self.TEST_PASSWORD)

        # Add the test user to the "agreed to terms" group, so tests can
        # run as if the user already accepted the PlantShare Terms.
        self.group.user_set.add(self.user)

        # Set up test data.

        family = Family(name='TestFamily')
        family.save()
        genus = Genus(name='TestGenus', family=family)
        genus.save()

        taxon = Taxon(scientific_name='Calystegia spithamaea', family=family,
            genus=genus)
        taxon.save()
        common_name = CommonName(common_name='upright false bindweed',
            taxon=taxon)
        common_name.save()
        synonym = Synonym(scientific_name='Convolvulus spithamaeus',
            full_name='Convolvulus spithamaeus L.', taxon=taxon)
        synonym.save()

        conservation_status = ConservationStatus(taxon=taxon, region='CT',
            allow_public_posting=True)
        conservation_status.save()

        conservation_status = ConservationStatus(taxon=taxon, region='NH',
            allow_public_posting=True)
        conservation_status.save()

        conservation_status = ConservationStatus(taxon=taxon, region='MA',
            allow_public_posting=False)
        conservation_status.save()

        # From a bug fixed with Issue #526: a subsp., but without restriction
        conservation_status = ConservationStatus(taxon=taxon, region='MA',
            variety_subspecies_hybrid='ssp. spithamaea',
            allow_public_posting=True)
        conservation_status.save()

        conservation_status = ConservationStatus(taxon=taxon, region='ME',
            allow_public_posting=True)
        conservation_status.save()

        conservation_status = ConservationStatus(taxon=taxon, region='RI',
            allow_public_posting=True)
        conservation_status.save()

        conservation_status = ConservationStatus(taxon=taxon, region='VT',
            allow_public_posting=False)
        conservation_status.save()

    def _get_restrictions(self, url_params, username=TEST_USERNAME,
            password=TEST_PASSWORD):
        """Get a sightings restrictions API response."""
        url = self.URL_BASE + url_params
        client = Client()
        client.login(username=username, password=password)
        return client.get(url)

    def test_restricted_scientific_name_new_england(self):
        response = self._get_restrictions(
            'plant=calystegia+spithamaea&location=Boston,%20MA')
        json_object = json.loads(response.content)
        self.assertTrue(json_object[0]['sightings_restricted'])

    def test_restricted_scientific_name_new_england_2(self):
        response = self._get_restrictions(
            'plant=calystegia+spithamaea&location=Burlington,%20VT')
        json_object = json.loads(response.content)
        self.assertTrue(json_object[0]['sightings_restricted'])

    def test_restricted_synonym_new_england(self):
        response = self._get_restrictions(
            'plant=convolvulus+spithamaeus&location=Boston,%20MA')
        json_object = json.loads(response.content)
        self.assertTrue(json_object[0]['sightings_restricted'])

    def test_restricted_synonym_new_england_2(self):
        response = self._get_restrictions(
            'plant=convolvulus+spithamaeus&location=Burlington,%20VT')
        json_object = json.loads(response.content)
        self.assertTrue(json_object[0]['sightings_restricted'])

    def test_restricted_common_name_new_england(self):
        response = self._get_restrictions(
            'plant=upright+false+bindweed&location=Boston,%20MA')
        json_object = json.loads(response.content)
        self.assertTrue(json_object[0]['sightings_restricted'])

    def test_restricted_common_name_new_england_2(self):
        response = self._get_restrictions(
            'plant=upright+false+bindweed&location=Burlington,%20VT')
        json_object = json.loads(response.content)
        self.assertTrue(json_object[0]['sightings_restricted'])

    def test_unrestricted_scientific_name_new_england(self):
        response = self._get_restrictions(
            'plant=calystegia+spithamaea&location=Danbury,%20CT')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])

    def test_unrestricted_scientific_name_new_england_2(self):
        response = self._get_restrictions(
            'plant=calystegia+spithamaea&location=Providence,%20RI')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])

    def test_unrestricted_synonym_new_england(self):
        response = self._get_restrictions(
            'plant=convolvulus+spithamaeus&location=Danbury,%20CT')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])

    def test_unrestricted_synonym_new_england_2(self):
        response = self._get_restrictions(
            'plant=convolvulus+spithamaeus&location=Providence,%20RI')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])

    def test_unrestricted_common_name_new_england(self):
        response = self._get_restrictions(
            'plant=upright+false+bindweed&location=Danbury,%20CT')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])

    def test_unrestricted_common_name_new_england_2(self):
        response = self._get_restrictions(
            'plant=upright+false+bindweed&location=Providence,%20RI')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])

    def test_restricted_and_flagged_when_in_restricted_state(self):
        response = self._get_restrictions(
            'plant=calystegia+spithamaea&location=Boston,%20MA')
        json_object = json.loads(response.content)
        self.assertTrue(json_object[0]['sightings_restricted'])
        self.assertTrue(json_object[0]['sightings_flagged'])

    def test_only_flagged_when_outside_restricted_state_and_region(self):
        # This state exists outside the region for which there are
        # conservation status data, so flagging for review is just an
        # extra safety check, mainly for bordering states and provinces.
        response = self._get_restrictions(
            'plant=calystegia+spithamaea&location=Orlando,%20FL')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])
        self.assertTrue(json_object[0]['sightings_flagged'])

    def test_not_flagged_when_outside_restricted_state_within_region(self):
        # This state is known to not need restriction, so no admin. review
        # should be needed.
        response = self._get_restrictions(
            'plant=calystegia+spithamaea&location=Providence,%20RI')
        json_object = json.loads(response.content)
        self.assertFalse(json_object[0]['sightings_restricted'])
        self.assertFalse(json_object[0]['sightings_flagged'])
