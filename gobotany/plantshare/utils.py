import json
import re
import urllib2

from itertools import chain

from django.conf import settings

from gobotany.core.models import Taxon
from gobotany.site.utils import query_regex

def get_covered_state(location):
    """Return the name of the state covered by the site for a given
    location, if possible.
    (So far below, ZIP code and state abbreviation/name support is
    limited to the New England states.)
    """
    state = None
    location = location.lower() if location else None

    if location:
        lat_long = re.search(r'^(-?\d{1,3}.?\d{1,6}?),? ?'
                              '(-?\d{1,3}.?\d{1,6}?)$', location)
        if lat_long:
            # Determine the state name from latitude and longitude
            # coordinates.
            latitude = lat_long.group(1)
            longitude = lat_long.group(2)
            url = ('http://data.fcc.gov/api/block/find?format=json&'
                   'latitude=%s&longitude=%s&showall=true') % (latitude,
                                                               longitude)
            try:
                data = urllib2.urlopen(url).read()
                response = json.loads(data)
                state = response['State']['name']
            except urllib2.HTTPError, e:
                print 'HTTP error: %d' % e.code
            except urllib2.URLError, e:
                print 'Network error: %s' % e.reason.args[1]
        elif re.search(r'\d{5}(-\d{4})?$', location):
            # Determine the state name from a ZIP code.
            if re.search(r'06[0-9]{3}(-\d{4})?$', location):
                state = 'Connecticut'
            elif re.search(r'0(39|40|41|42|43|44|45|46|47|48|49)[0-9]{2}'
                            '(-\d{4})?$', location):
                state = 'Maine'
            elif re.search(r'0(10|11|12|13|14|15|16|17|18|19|20|21|22|23|'
                            '24|25|26|27)[0-9]{2}(-\d{4})?$', location):
                state = 'Massachusetts'
            elif re.search(r'03[0-8]{1}[0-9]{2}(-\d{4})?$', location):
                state = 'New Hampshire'
            elif re.search(r'02[89]{1}[0-9]{2}(-\d{4})?$', location):
                state = 'Rhode Island'
            elif re.search(r'05[0-9]{3}(-\d{4})?$', location):
                state = 'Vermont'
        else:
            # Determine the state name from a name or abbreviation.
            if re.search(r'\W(connecticut|ct\.?|conn\.?)$', location):
                state = 'Connecticut'
            elif re.search(r'\W(maine|me\.?)$', location):
                state = 'Maine'
            elif re.search(r'\W(massachusetts|ma\.?|mass\.?)$', location):
                state = 'Massachusetts'
            elif re.search(r'\W(new\s+hampshire|nh|n\.?\s+h\.?)$', location):
                state = 'New Hampshire'
            elif re.search(r'\W(rhode\s+island|ri|r\.?\s+i\.?)$', location):
                state = 'Rhode Island'
            elif re.search(r'\W(vermont|vt\.?)$', location):
                state = 'Vermont'

    state = state if state in [
        v for k, v in settings.STATE_NAMES.iteritems()] else None

    return state

def restrictions(plant_name, location=None):
    """Return a list of taxa matching a given plant name, along with any
    information on restrictions for sightings of rare plants, etc.
    """
    plant_regex = query_regex(plant_name, anchor_at_start=True,
        anchor_at_end=True)
    covered_state = get_covered_state(location)
    restrictions = []

    scientific_name_taxa = Taxon.objects.filter(
        scientific_name__iregex=plant_regex)
    common_name_taxa = Taxon.objects.filter(
        common_names__common_name__iregex=plant_regex)
    synonym_taxa = Taxon.objects.filter(
        synonyms__scientific_name__iregex=plant_regex)
    taxa = list(
        set(chain(scientific_name_taxa, common_name_taxa, synonym_taxa)))

    for taxon in taxa:
        common_names = [n.common_name for n in taxon.common_names.all()]
        synonyms = [s.scientific_name for s in taxon.synonyms.all()]

        allow_public_posting = {}
        for status in taxon.conservation_statuses.all():
            state_name = settings.STATE_NAMES[status.region.lower()]
            allow_public_posting[state_name] = status.allow_public_posting
        # Fill in any states that do not have conservation status
        # records.
        for key in settings.STATE_NAMES.keys():
            state_name = settings.STATE_NAMES[key]
            if state_name not in allow_public_posting.keys():
                allow_public_posting[state_name] = True

        sightings_restricted = False

        # If the location is in a state covered by the site, restrict
        # only if the plant is rare in that state.
        if covered_state is not None and covered_state:
            if not allow_public_posting[covered_state]:
                sightings_restricted = True
        else:
            # If the location is anywhere else (or is unknown), restrict
            # if the plant is rare in any New England state, as a fallback.
            # This is a conservative measure for various edge cases
            # such as plants that may be rare outside New England,
            # incorrect location detection, etc.
            for state in allow_public_posting.keys():
                if not allow_public_posting[state]:
                    sightings_restricted = True
                    break

        restrictions.append({
            'scientific_name': taxon.scientific_name,
            'common_names': common_names,
            'synonyms': synonyms,
            'covered_state': covered_state,
            'allow_public_posting': allow_public_posting,
            'sightings_restricted': sightings_restricted,
        })

    return restrictions
