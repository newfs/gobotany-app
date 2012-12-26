import json
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
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
def pile_characters(request, pile_slug):
    return render_to_response('gobotany/pile_characters.html', {
        'common_characters': models.Character.objects.filter(
            short_name__in=models.COMMON_CHARACTERS),
        'pile' : get_object_or_404(models.Pile, slug=pile_slug),
        }, context_instance=RequestContext(request))

@permission_required('botanist')
def edit_pile_character(request, pile_slug, character_slug):

    character = get_object_or_404(models.Character, short_name=character_slug)
    values = sorted(character.character_values.all(), key=character_value_key)

    pile = get_object_or_404(models.Pile, slug=pile_slug)
    taxa = list(pile.species.all())

    tcvlist = list(models.TaxonCharacterValue.objects
                   .filter(taxon__in=taxa, character_value__in=values))
    value_map = {(tcv.taxon_id, tcv.character_value_id): tcv
                 for tcv in tcvlist}

    # We now have enough information, and can either handle a POST
    # update of specific data or a GET that displays the whole pile.

    if 'vectors' in request.POST:
        taxa_by_name = { taxon.scientific_name: taxon for taxon in taxa }
        vectors = json.loads(request.POST['vectors'])

        for name, vector in vectors:
            scientific_name = ' '.join(name.split()[:2])
            taxon = taxa_by_name[scientific_name]
            for digit, value in zip(vector, values):
                key = (taxon.id, value.id)
                if digit == '0' and key in value_map:
                    value_map[key].delete()
                elif digit == '1' and key not in value_map:
                    models.TaxonCharacterValue(
                        taxon=taxon, character_value=value
                        ).save()

        return redirect(request.path)

    # Grabbing one copy of each family once is noticeably faster than
    # using select_related('family') up in the taxon fetch:

    family_ids = set(t.family_id for t in taxa)
    families = models.Family.objects.filter(id__in=family_ids)

    taxa.sort(key=pluck('family_id'))  # always sort() before groupby()!
    taxa_by_family_id = { family_id: list(group) for family_id, group
                          in groupby(taxa, key=pluck('family_id')) }

    partner = which_partner(request)
    simple_ids = set(ps.species_id for ps in models.PartnerSpecies.objects
                     .filter(partner_id=partner.id, simple_key=True))

    # This view takes far too long to render with slow Django templates,
    # so we simply deliver JSON data for the front-end to render there.

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
    taxa_ids = set(taxon.id for taxon in taxa)

    coverage_percent_full = len(taxa_with_values) * 100.0 / len(taxa)
    coverage_percent_simple = (len(simple_ids.intersection(taxa_with_values))
                     * 100.0 / len(simple_ids.intersection(taxa_ids)))

    return render_to_response('gobotany/edit_pile_character.html', {
        'there_are_any_friendly_texts': any(v.friendly_text for v in values),
        'character': character,
        'coverage_percent_full': coverage_percent_full,
        'coverage_percent_simple': coverage_percent_simple,
        'grid': json.dumps(list(grid())),
        'pile': pile,
        'values': values,
        'values_json': json.dumps([value.value_str for value in values]),
        }, context_instance=RequestContext(request))

@permission_required('botanist')
def pile_taxa(request, pile_slug):
    return render_to_response('gobotany/pile_taxa.html', {
        'pile' : get_object_or_404(models.Pile, slug=pile_slug),
        }, context_instance=RequestContext(request))

@permission_required('botanist')
def edit_pile_taxon(request, pile_slug, taxon_slug):

    name = taxon_slug.capitalize().replace('-', ' ')

    pile = get_object_or_404(models.Pile, slug=pile_slug)
    taxon = get_object_or_404(models.Taxon, scientific_name=name)

    # We build a list of characters.
    # Each character has .values, a sorted list of character values
    # Each value has .checked, indicating that the species has it.

    return render_to_response('gobotany/edit_pile_taxon.html', {
        'pile': pile,
        'taxon': taxon,
        }, context_instance=RequestContext(request))

def character_value_key(cv):
    """Return a sort key that puts 'NA' last."""

    if cv.value_str == 'NA':
        return 'zzzz'
    return cv.value_str
