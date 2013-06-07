from itertools import chain

from gobotany.core.models import Taxon

RESTRICTED_STATUSES = ['rare', 'endangered', 'threatened',
    'special concern', 'historic', 'extirpated']

def restrictions(plant_name):
    """Return a list of taxa matching a given plant name, along with any
    information on restrictions for sightings of rare plants, etc.
    """

    # Remove any extra spaces in the plant name.
    plant_name = ' '.join(plant_name.split())

    # Split the words and create regular expressions for typo matching:
    # - Interior transpositions: pylmouth rose-gentian, plymouth rsoe-gentian
    # - An extra character: plymoutth rose-gentian
    # - A missing duplicate character: sabatia kenedyana (missing an 'n')
    regex_words = []
    words = plant_name.split()
    for word in words:
        if len(word) > 2:
            interior = ''.join(set(list(word[1:-1]))) # Unique interior chars.
            regex_word = '%s[%s]{%d,%d}%s' % (
                word[0],   # First character: an anchor
                interior,  # Any interior characters, to handle transpositions
                len(interior),      # Allow typo with an extra character
                len(interior) + 1,
                word[-1])  # Last character: another anchor
        else:
            regex_word = word
        regex_words.append(regex_word)

    # Allow ignoring hyphens, periods, and other non-word characters.
    plant_name_regex = '\W+'.join(regex_words)

    restrictions = []

    scientific_name_taxa = Taxon.objects.filter(
        scientific_name__iregex=plant_name_regex)
    common_name_taxa = Taxon.objects.filter(
        common_names__common_name__iregex=plant_name_regex)
    synonym_taxa = Taxon.objects.filter(
        synonyms__scientific_name__iregex=plant_name_regex)
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
        restricted_by = [restricted_status for restricted_status
            in RESTRICTED_STATUSES if restricted_status in
            '\n'.join(all_statuses)]
        if len(restricted_by) > 0:
            sightings_restricted = True

        restrictions.append({
            "scientific_name": taxon.scientific_name,
            "common_names": common_names,
            "synonyms": synonyms,
            "all_statuses": all_statuses,
            "restricted_by": restricted_by,
            "sightings_restricted": sightings_restricted,
        })

    return restrictions
