'''An implementation of Information Gain and Decision Tree compilation.
Much of the implementation was pulled from the (assumed) public domain
code located at:
  http://onlamp.com/python/2006/02/09/examples/dtree.tar.gz
  http://onlamp.com/pub/a/python/2006/02/09/ai_decision_trees.html?page=1
'''
import math
from collections import defaultdict

from gobotany.core.models import Character, Parameter, TaxonCharacterValue

def compute_character_entropies(pile, species_list):
    """Find the most effective characters for narrowing down these species.

    A list of tuples is returned, each of which looks like::

        (character_id, entropy, coverage)

    """
    # We start by fetching the character values for this pile (ignoring
    # "NA" values, since they really state that a character doesn't
    # apply to a species), and then selecting the TaxonCharacterValue
    # rows that match one of these character values with one of the
    # species given in `species_list`.

    cv_list = list(pile.character_values
                   .exclude(value_str='NA')
                   .exclude(value_min=0.0, value_max=0.0))
    taxon_character_values = TaxonCharacterValue.objects.filter(
        taxon__in=species_list, character_value__in=cv_list)

    # Since Django's ORM will stupidly re-query the database if we ask
    # for the ".character_value" of one of these TaxonCharacterValue
    # objects, we put these character values in a dictionary by ID so
    # that we can get them more quickly ourselves.  We also go ahead and
    # group them by character_id.

    cv_by_id = {}
    cv_by_character_id = defaultdict(set)
    for cv in cv_list:
        cv_by_id[cv.id] = cv
        cv_by_character_id[cv.character_id].add(cv)

    # To compute a character's entropy, we need to know two things:
    #
    # 1. How many species total are touched by that character's values.
    #    If a particular species is linked to two of the character's
    #    values ("this plant has blue flowers AND red flowers"), then
    #    the species still only gets counted once.
    #
    #    So we create a "character_species" dictionary that maps
    #    character IDs to species-ID sets, and count the length of each
    #    set of species IDs when we are done.
    #
    # 2. How many times each character value is used.  So we create a
    #    character_value_counts dictionary.
    #
    # Both of these data structures are populated very simply, by
    # iterating once across our taxon_character_values query.

    character_species = defaultdict(set)
    cv_counts = defaultdict(int)

    for tcv in taxon_character_values:
        cv = cv_by_id[tcv.character_value_id]
        character_species[cv.character_id].add(tcv.taxon_id)
        cv_counts[cv] += 1

    # Finally, we are ready to compute the entropies!  We tally up the
    # value "n * log n" for each character value in a character, then
    # divide the result by the total number of species touched by that
    # character.  We also throw in to our result, just for good measure,
    # a "coverage" fraction indicating how many of the species we are
    # looking at are touched by each character.

    n = float(len(species_list))

    result = []
    for character_id, cv_set in cv_by_character_id.items():
        species_set = character_species[character_id]

        # To avoid the expense of fetching characters from the database,
        # we use a random character value to guess whether this is a
        # textual or numeric character.

        cv = iter(cv_set).next()  # random element without removing it
        if cv.value_str is not None:
            ne = _text_entropy(cv_set, species_set, cv_counts)
        elif cv.value_min is not None or cv.value_max is not None:
            ne = _length_entropy(cv_set, species_set, cv_counts)
        else:
            ne = 1e10  # hopefully someone reviewing best-characters notices

        entropy = ne / n
        coverage = len(species_set) / n
        result.append((character_id, entropy, coverage))

    return result


def _text_entropy(cv_set, species_set, cv_counts):
    """Compute the info-gain from choosing a value of a text character."""
    tally = 0.0
    for cv in cv_set:
        count = cv_counts[cv]
        if count:
            tally += count * math.log(count, 2.)
    return tally


def _length_entropy(cv_set, species_set, cv_counts):
    """Compute the info-gain from choosing a value of a length character."""
    #
    # This routine runs along a range of length values, and pretends
    # that each possible length (4mm, 5mm, 6mm, ...) in the range is its
    # own character value, and then applies the normal entropy
    # calculation to this set of pretend character values.
    #
    # Imagine that we have two ranges like this:
    #
    # 2   3   4   5   6   7   8   9
    # |-------------------|
    #             |---------------|
    #
    # The technique of the algorithm below is first to reduce this to a
    # list of endpoints, at which the number of active ranges either
    # increases or decreases:
    #
    # [ (2,+1), (5,+1), (7,-1), (9,-1) ]
    #
    # Then we can run along this range, keeping a tally that is adjusted
    # up and down by the +1s and -1s, and know how to weight each range
    # by both its length (which we get by subtracting the coordinate of
    # adjacent endpoints ) and the number of species inside (which is
    # the value of the running +- count).
    #
    endpoints = []
    for cv in cv_set:
        if cv.value_min is None or cv.value_max is None:
            continue
        if cv.value_min > cv.value_max:
            print '    Skipped invalid range: min %.1f, max %.1f' % \
                (cv.value_min, cv.value_max)
            continue
        endpoints.append((cv.value_min, +1))
        endpoints.append((cv.value_max, -1))
    endpoints.sort()

    i = iter(endpoints)
    left, weight = i.next()  # the first endpoint
    tally = 0.0

    for endpoint in i:  # the rest of the endpoints
        right, increment = endpoint

        size = right - left
        if size and weight:
            tally += size * weight * math.log(weight, 2.)

        left = right
        weight += increment

    tally /= endpoints[-1][0] - endpoints[0][0]
    return tally


def compute_score(entropy, coverage, ease, value_type,
                  coverage_weight, ease_weight, length_weight):
    """Our secret formula for deciding which characters are best!"""
    score = (entropy
             + 10. * (1. - coverage) * coverage_weight
             + 0.1 * ease_weight * ease)
    if value_type == u'LENGTH':
        score /= length_weight  # so that a high weight makes a better score
    return score


def get_weights():
    """Return the two weight parameters related to scoring."""
    coverage_weight = 0.7
    ease_weight = 2.0
    length_weight = 0.4
    names = (
        'coverage_weight', 'ease_of_observability_weight', 'length_weight',
        )
    for parameter in Parameter.objects.filter(name__in=names):
        if parameter.name == 'coverage_weight':
            coverage_weight = parameter.value
        elif parameter.name == 'ease_of_observability_weight':
            ease_weight = parameter.value
        elif parameter.name == 'length_weight':
            length_weight = parameter.value
    return coverage_weight, ease_weight, length_weight

def rank_characters(pile, species_list):
    """Returns a list of (score, entropy, coverage, character), best first."""
    celist = compute_character_entropies(pile, species_list)
    result = []

    coverage_weight, ease_weight, length_weight = get_weights()

    for character_id, entropy, coverage in celist:
        character = Character.objects.get(id=character_id)
        if character.value_type not in (u'TEXT', u'LENGTH'):
            continue  # skip non-textual filters
        ease = character.ease_of_observability
        score = compute_score(entropy, coverage, ease, character.value_type,
                              coverage_weight, ease_weight, length_weight)
        result.append((score, entropy, coverage, character))

    result.sort()
    return result
