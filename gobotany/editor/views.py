import json
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from itertools import groupby
from operator import attrgetter as pluck

from gobotany.core import models
from gobotany.core.partner import which_partner

def e404(request):
    raise Http404()

@permission_required('botanist')
def piles_view(request):
    return render_to_response('gobotany/edit_piles.html', {
        'piles' : models.Pile.objects.all(),
        }, context_instance=RequestContext(request))

@permission_required('botanist')
def pile_view(request, pile_slug):
    return render_to_response('gobotany/edit_pile.html', {
        'general_characters': models.Character.objects.filter(
            short_name__in=models.COMMON_CHARACTERS),
        'pile' : get_object_or_404(models.Pile, slug=pile_slug),
        }, context_instance=RequestContext(request))

@permission_required('botanist')
def edit_pile_character(request, pile_slug, character_slug):

    # This view takes far too long to render with slow Django templates,
    # so we simply deliver JSON data for the front-end to render there.

    character = get_object_or_404(models.Character, short_name=character_slug)
    values = sorted(character.character_values.all(), key=character_value_key)

    pile = get_object_or_404(models.Pile, slug=pile_slug)
    taxa = list(pile.species.all())

    tcvlist = models.TaxonCharacterValue.objects.filter(
        taxon__in=taxa, character_value__in=values)
    value_map = set((tcv.taxon_id, tcv.character_value_id) for tcv in tcvlist)

    # Grabbing each family once is faster than using select_related() up
    # in the taxon fetch:

    family_ids = set(t.family_id for t in taxa)
    families = models.Family.objects.filter(id__in=family_ids)

    taxa.sort(key=pluck('family_id'))  # always sort() before groupby()!
    taxa_by_family_id = { family_id: list(group) for family_id, group
                          in groupby(taxa, key=pluck('family_id')) }

    partner = which_partner(request)
    simple_ids = set(ps.species_id for ps in models.PartnerSpecies.objects
                     .filter(partner_id=partner.id, simple_key=True))

    def grid():
        for family in sorted(families, key=pluck('name')):
            yield [family.name]
            family_taxa = taxa_by_family_id[family.id]
            for taxon in family_taxa:
                vector = ''.join(
                    '1' if (taxon.id, value.id) in value_map else '0'
                    for value in values
                    )
                name = taxon.scientific_name
                if taxon.id not in simple_ids:
                    name += ' (fk)'
                yield [name, vector]

    taxa_with_values = set(tcv.taxon_id for tcv in tcvlist)
    coverage_percent = len(taxa_with_values) * 100.0 / len(taxa)

    return render_to_response('gobotany/edit_pile_character.html', {
        'there_are_any_friendly_texts': any(v.friendly_text for v in values),
        'character': character,
        'coverage_percent': coverage_percent,
        'grid': json.dumps(list(grid())),
        'pile': pile,
        'values': values,
        'values_json': json.dumps([value.value_str for value in values]),
        }, context_instance=RequestContext(request))

def character_value_key(cv):
    """Return a sort key that puts 'NA' last."""

    if cv.value_str == 'NA':
        return 'zzzz'
    return cv.value_str
