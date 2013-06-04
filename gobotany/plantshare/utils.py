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

    restrictions = []

    scientific_name_taxa = Taxon.objects.filter(
        scientific_name__iexact=plant_name)
    common_name_taxa = Taxon.objects.filter(
        common_names__common_name__iexact=plant_name)
    synonym_taxa = Taxon.objects.filter(
        synonyms__scientific_name__iexact=plant_name)
    taxa = list(chain(scientific_name_taxa, common_name_taxa, synonym_taxa))

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
