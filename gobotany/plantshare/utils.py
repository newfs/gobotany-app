import re

from itertools import chain

from gobotany.core.models import Taxon
from gobotany.site.utils import query_regex

RESTRICTED_STATUSES = ['rare', 'endangered', 'threatened',
    'special concern', 'historic', 'extirpated']

def new_england_state(location):
    """Return the New England state for a location."""
    state = None
    location = location.lower() if location else None

    # Determine the state name from the end of the location string.
    if location:
        if re.search(r'\W(connectitcut|ct\.?|conn\.?)$', location):
            state = 'Connecticut'
        elif re.search(r'\W(massachusetts|ma\.?|mass\.?)$', location):
            state = 'Massachusetts'
        elif re.search(r'\W(maine|me\.?)$', location):
            state = 'Maine'
        elif re.search(r'\W(new\s+hampshire|nh|n\.?\s+h\.?)$', location):
            state = 'New Hampshire'
        elif re.search(r'\W(rhode\s+island|ri|r\.?\s+i\.?)$', location):
            state = 'Rhode Island'
        elif re.search(r'\W(vermont|vt\.?)$', location):
            state = 'Vermont'

    return state

def restrictions(plant_name, location=None):
    """Return a list of taxa matching a given plant name, along with any
    information on restrictions for sightings of rare plants, etc.
    """
    plant_regex = query_regex(plant_name)
    ne_state = new_england_state(location)
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

        statuses = taxon.get_conservation_statuses()
        statuses_lists = [v for k, v in
            {k : v for k, v in statuses.iteritems()}.iteritems()]
        all_statuses = list(set(list(chain.from_iterable(statuses_lists))))

        sightings_restricted = False
        restricted_by = []

        # If the location is in a New England state, restrict only if
        # the plant is rare in that state.

        if ne_state is not None and ne_state:
            restricted_list = statuses[ne_state]
        else:
            # If the location is anywhere else (or is unknown), restrict
            # if the plant is rare in any New England state, as a fallback.
            # This is a conservative measure for various edge cases
            # such as plants that may be rare outside New England,
            # incorrect location detection, etc.
            restricted_list = all_statuses

        restricted_by = [restricted_status for restricted_status
            in RESTRICTED_STATUSES if restricted_status in restricted_list]
        if len(restricted_by) > 0:
            sightings_restricted = True

        restrictions.append({
            'scientific_name': taxon.scientific_name,
            'common_names': common_names,
            'synonyms': synonyms,
            'new_england_state': ne_state,
            'statuses': statuses,
            'all_statuses': all_statuses,
            'restricted_by': restricted_by,
            'sightings_restricted': sightings_restricted,
        })

    return restrictions
