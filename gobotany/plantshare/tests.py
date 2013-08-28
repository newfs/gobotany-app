"""Basic PlantShare functional tests that do not require a browser."""

import json
import unittest

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.test.client import Client

from selenium.common.exceptions import NoSuchElementException

from gobotany.libtest import FunctionalCase

from gobotany.core.models import (ConservationStatus, CommonName, Family,
    Genus, Synonym, Taxon)
from gobotany.plantshare.models import Location

class PlantShareTests(FunctionalCase):

    PLANTSHARE_BASE = '/plantshare'

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

    def _get_plantshare(self, url_path, log_in=False, username=TEST_USERNAME,
                        password=TEST_PASSWORD):
        """Get a PlantShare page."""
        url = self.PLANTSHARE_BASE + url_path
        client = None
        if log_in:
            client = Client()
            client.login(username=username, password=password)
        self.get(url, client=client)

    # Test helpers

    def _page_title(self, url_path, log_in=False):
        """Return the HTML title for a page."""
        self._get_plantshare(url_path, log_in=log_in)
        return self.css1('title').text

    def _page_heading(self, url_path, log_in=False):
        """Return the main (h1) heading for a page."""
        self._get_plantshare(url_path, log_in=log_in)
        return self.css1('h1').text

    ### TESTS ###

    # PlantShare main page

    MAIN_URL = '/'

    def test_main_page_title(self):
        self.assertEqual(self._page_title(self.MAIN_URL),
                         'PlantShare: Go Botany')

    def test_main_page_main_heading(self):
        self.assertEqual(self._page_heading(self.MAIN_URL), 'PlantShare')

    # PlantShare main page: when user is logged out

    def test_main_page_logged_out_has_signup_nav_link(self):
        self._get_plantshare(self.MAIN_URL)
        self.assertIsNotNone(self.link_saying('Sign Up for PlantShare'))

    def test_main_page_logged_out_has_signup_call_to_action(self):
        self._get_plantshare(self.MAIN_URL)
        self.assertTrue(self.css1('.sign-up-call'))

    def test_main_page_logged_out_has_login_form(self):
        self._get_plantshare(self.MAIN_URL)
        self.assertTrue(self.css1('#login.box'))

    def test_main_page_logged_out_omits_profile_box(self):
        self._get_plantshare(self.MAIN_URL)
        profile_box = None
        try:
            profile_box = self.css1('.profile.box')
        except NoSuchElementException:
            pass
        self.assertIsNone(profile_box)

    def test_main_page_logged_out_omits_profile_nav_link(self):
        self._get_plantshare(self.MAIN_URL)
        link = None
        try:
            link = self.link_saying('Your Profile')
        except ValueError:
            pass
        self.assertIsNone(link)

    def test_main_page_logged_out_omits_logout_link(self):
        self._get_plantshare(self.MAIN_URL)
        link = None
        try:
            link = self.link_saying('Log Out')
        except ValueError:
            pass
        self.assertIsNone(link)

    # PlantShare main page: when user is logged in

    def test_main_page_logged_in_has_profile_box(self):
        self._get_plantshare(self.MAIN_URL, log_in=True)
        self.assertTrue(self.css1('.profile.box'))

    def test_main_page_logged_in_has_profile_nav_item(self):
        self._get_plantshare(self.MAIN_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Your Profile'))

    def test_main_page_logged_in_has_logout_nav_item(self):
        self._get_plantshare(self.MAIN_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Log Out ' +
                                              self.TEST_USERNAME))

    def test_main_page_logged_in_omits_signup_nav_item(self):
        self._get_plantshare(self.MAIN_URL, log_in=True)
        link = None
        try:
            link = self.link_saying('Sign Up for PlantShare')
        except ValueError:
            pass
        self.assertIsNone(link)

    def test_main_page_logged_in_omits_signup_call_to_action(self):
        self._get_plantshare(self.MAIN_URL, log_in=True)
        call_to_action = None
        try:
            call_to_action = self.css1('.sign-up-call')
        except NoSuchElementException:
            pass
        self.assertIsNone(call_to_action)

    def test_main_page_logged_in_omits_login_form(self):
        self._get_plantshare(self.MAIN_URL, log_in=True)
        form = None
        try:
            form = self.css1('#login.box')
        except NoSuchElementException:
            pass
        self.assertIsNone(form)

    # Log In page: used only for login errors or when users attempt to
    # visit a URL that requires login. The usual place to log in is the
    # form in the sidebthe PlantShare main page.

    LOG_IN_URL = '/accounts/login/'

    def test_login_page_title(self):
        self.assertEqual(self._page_title(self.LOG_IN_URL),
                         'Log In: PlantShare: Go Botany')

    def test_login_page_main_heading(self):
        self.assertEqual(self._page_heading(self.LOG_IN_URL), 'Log In')

    def test_login_page_has_plantshare_nav_link(self):
        self._get_plantshare(self.LOG_IN_URL)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_login_page_has_minimal_navigation(self):
        self._get_plantshare(self.LOG_IN_URL)
        navigation_items = self.css('#sidebar nav li')
        self.assertEqual(len(navigation_items), 1)

    def test_login_page_has_message_requesting_login_to_continue(self):
        self._get_plantshare(self.MY_PROFILE_URL)   # A page requiring login
        message = self.css1('h1 + p').text
        self.assertEqual(message, 'Please log in to continue.')

    def test_login_page_occurs_upon_bad_login(self):
        self._get_plantshare(self.MY_PROFILE_URL, log_in=True,
                             username='nobody', password='nothing')
        heading = self.css1('h1').text
        self.assertEqual(heading, 'Log In')

    # Log Out confirmation page

    LOG_OUT_URL = '/accounts/logout/'

    def test_log_out_page_title(self):
        self.assertEqual(self._page_title(self.LOG_OUT_URL),
                         'Logged Out: PlantShare: Go Botany')

    def test_log_out_page_main_heading(self):
        self.assertEqual(self._page_heading(self.LOG_OUT_URL), 'Logged Out')

    def test_log_out_page_has_plantshare_nav_item(self):
        self._get_plantshare(self.LOG_OUT_URL)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_log_out_page_has_basic_navigation(self):
        # The Logged Out page should show the basic PlantShare
        # navigation elements that appear when a user is logged out.
        self._get_plantshare(self.LOG_OUT_URL)
        navigation_items = self.css('#sidebar nav li')
        self.assertEqual(len(navigation_items), 5)

    # Sign Up for PlantShare page

    SIGNUP_FORM_URL = '/accounts/register/'

    def test_signup_page_title(self):
        self.assertEqual(self._page_title(self.SIGNUP_FORM_URL),
                         'Sign Up for PlantShare: Go Botany')

    def test_signup_page_main_heading(self):
        self.assertEqual(self._page_heading(self.SIGNUP_FORM_URL),
                         'Sign Up for PlantShare')

    def test_signup_page_has_plantshare_nav_item(self):
        self._get_plantshare(self.SIGNUP_FORM_URL)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_signup_page_has_minimal_navigation(self):
        self._get_plantshare(self.SIGNUP_FORM_URL)
        navigation_items = self.css('#sidebar nav li')
        self.assertEqual(len(navigation_items), 2)   # includes Signup item

    @unittest.skip('Skip for now: test requires reaching a server on the Web')
    def test_sign_up_with_incorrect_captcha_response(self):
        form_submit_url = self.PLANTSHARE_BASE + self.SIGNUP_FORM_URL
        client = Client()
        response = client.post(form_submit_url, {'username': 'test2',
            'email': 'test2@test2.net', 'password1': 'testpass2',
            'password2': 'testpass2',
            'recaptcha_response_field': 'spam eggs'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.content.find('Incorrect, please try again.') > -1)

    # Registration Complete page (next step: activate from email)

    REG_COMPLETE_URL = '/accounts/register/complete/'

    def test_registration_complete_page_title(self):
        self.assertEqual(self._page_title(self.REG_COMPLETE_URL),
                         'Sign Up Complete: PlantShare: Go Botany')

    def test_registration_complete_page_main_heading(self):
        self.assertEqual(self._page_heading(self.REG_COMPLETE_URL),
                                            'Sign Up Complete')

    def test_registration_complete_page_has_plantshare_nav_item(self):
        self._get_plantshare(self.REG_COMPLETE_URL)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_registration_complete_page_has_minimal_navigation(self):
        self._get_plantshare(self.REG_COMPLETE_URL)
        navigation_items = self.css('#sidebar nav li')
        self.assertEqual(len(navigation_items), 1)

    # Activation Complete page

    ACTIVATION_COMPLETE_URL = '/accounts/activate/complete/'
    def test_activation_complete_page_title(self):
        self.assertEqual(self._page_title(self.ACTIVATION_COMPLETE_URL),
                         'Activation Complete: PlantShare: Go Botany')

    def test_activation_complete_page_main_heading(self):
        self.assertEqual(self._page_heading(self.ACTIVATION_COMPLETE_URL),
                         'Activation Complete')

    def test_activation_complete_page_has_plantshare_nav_item(self):
        self._get_plantshare(self.ACTIVATION_COMPLETE_URL)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_activation_complete_page_has_minimal_navigation(self):
        self._get_plantshare(self.ACTIVATION_COMPLETE_URL)
        navigation_items = self.css('#sidebar nav li')
        self.assertEqual(len(navigation_items), 1)

    # Post a (new) Sighting form page

    NEW_SIGHTING_URL = '/sightings/new/'

    def test_new_sighting_form_page_requires_login(self):
        self._get_plantshare(self.NEW_SIGHTING_URL, log_in=False)
        heading = self.css1('h1').text
        self.assertEqual(heading, 'Log In')

    def test_new_sighting_form_page_title(self):
        self.assertEqual(self._page_title(
            self.NEW_SIGHTING_URL, log_in=True),
            'Post a Sighting: PlantShare: Go Botany')

    def test_new_sighting_form_page_main_heading(self):
        self.assertEqual(self._page_heading(self.NEW_SIGHTING_URL,
                                            log_in=True), 'Post a Sighting')

    def test_new_sighting_form_page_has_plantshare_nav_item(self):
        self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_new_sighting_form_page_has_post_a_sighting_nav_item(self):
        self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Post a Sighting'))

    def test_new_sighting_form_page_has_my_profile_nav_item(self):
        self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Your Profile'))

    def test_new_sighting_form_page_has_full_navigation(self):
        self._get_plantshare(self.NEW_SIGHTING_URL, log_in=True)
        navigation_items = self.css('#sidebar nav li')
        self.assertGreater(len(navigation_items), 1)

    # Post a (new) Sighting: "done" page

    NEW_SIGHTING_DONE_URL = '/sightings/new/done/'

    def test_new_sighting_done_page_requires_login(self):
        self._get_plantshare(self.NEW_SIGHTING_DONE_URL, log_in=False)
        heading = self.css1('h1').text
        self.assertEqual(heading, 'Log In')

    def test_new_sighting_done_page_title(self):
        self.assertEqual(self._page_title(
            self.NEW_SIGHTING_DONE_URL, log_in=True),
            'Sighting Posted: PlantShare: Go Botany')

    def test_new_sighting_done_page_main_heading(self):
        self.assertEqual(self._page_heading(self.NEW_SIGHTING_DONE_URL,
                                            log_in=True), 'Sighting Posted')

    def test_new_sighting_done_page_has_plantshare_nav_item(self):
        self._get_plantshare(self.NEW_SIGHTING_DONE_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_new_sighting_done_page_has_post_a_sighting_nav_item(self):
        self._get_plantshare(self.NEW_SIGHTING_DONE_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Post a Sighting'))

    def test_new_sighting_done_page_has_my_profile_nav_item(self):
        self._get_plantshare(self.NEW_SIGHTING_DONE_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Your Profile'))

    def test_new_sighting_done_page_has_full_navigation(self):
        self._get_plantshare(self.NEW_SIGHTING_DONE_URL, log_in=True)
        navigation_items = self.css('#sidebar nav li')
        self.assertGreater(len(navigation_items), 1)

    # Your Profile page

    MY_PROFILE_URL = '/profile/'

    def test_profile_page_requires_login(self):
        self._get_plantshare(self.MY_PROFILE_URL, log_in=False)
        heading = self.css1('h1').text
        self.assertEqual(heading, 'Log In')

    def test_profile_page_title(self):
        self.assertEqual(self._page_title(
            self.MY_PROFILE_URL, log_in=True),
            'Your Profile: PlantShare: Go Botany')

    def test_profile_page_main_heading(self):
        self.assertEqual(self._page_heading(self.MY_PROFILE_URL,
                                            log_in=True), 'Your Profile')

    def test_profile_page_has_plantshare_nav_item(self):
        self._get_plantshare(self.MY_PROFILE_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('PlantShare'))

    def test_profile_page_has_post_a_sighting_nav_item(self):
        self._get_plantshare(self.MY_PROFILE_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Post a Sighting'))

    def test_profile_page_has_my_profile_nav_item(self):
        self._get_plantshare(self.MY_PROFILE_URL, log_in=True)
        self.assertIsNotNone(self.link_saying('Your Profile'))

    def test_my_profile_page_has_full_navigation(self):
        self._get_plantshare(self.MY_PROFILE_URL, log_in=True)
        navigation_items = self.css('#sidebar nav li')
        self.assertGreater(len(navigation_items), 1)


class LocationModelTests(TestCase):

    def test_location_save_parses_input_city_state(self):
        location = Location(user_input='Framingham, MA')
        location.save()
        self.assertEqual(location.city, 'Framingham')
        self.assertEqual(location.state, 'MA')

    def test_location_save_parses_input_zip_code(self):
        location = Location(user_input='01701')
        location.save()
        self.assertEqual(location.postal_code, '01701')

    def test_location_save_parses_input_zip_plus_four(self):
        location = Location(user_input='01701-2699')
        location.save()
        self.assertEqual(location.postal_code, '01701-2699')

    def test_location_save_parses_input_canadian_postal_code(self):
        location = Location(user_input='E7B 1A3')
        location.save()
        self.assertEqual(location.postal_code, 'E7B 1A3')

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
        self.assertIsNone(location.city)
        self.assertIsNone(location.state)
        self.assertIsNone(location.postal_code)
        self.assertIsNone(location.latitude)
        self.assertIsNone(location.longitude)

    def test_location_save_parses_input_ignores_garbage_numbers(self):
        location = Location(user_input='12873498712983749182')
        location.save()
        self.assertIsNone(location.city)
        self.assertIsNone(location.state)
        self.assertIsNone(location.postal_code)
        self.assertIsNone(location.latitude)
        self.assertIsNone(location.longitude)

    def test_location_save_parses_input_ignores_garbage_mixed(self):
        location = Location(user_input='aoeua87aoe349a8712b8qjk37a')
        location.save()
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
