import json
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from gobotany.core import models

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

    pile = get_object_or_404(models.Pile, slug=pile_slug)
    character = get_object_or_404(models.Character, short_name=character_slug)

    taxa = list(pile.species.all())
    values = sorted(character.character_values.all(), key=character_value_key)
    tcvlist = models.TaxonCharacterValue.objects.filter(
        taxon__in=taxa, character_value__in=values)

    value_map = set((tcv.taxon_id, tcv.character_value_id) for tcv in tcvlist)

    vectors = {}
    for taxon in taxa:
        vectors[taxon.scientific_name] = ''.join(
            '1' if (taxon.id, value.id) in value_map else '0'
            for value in values
            )

    taxa_with_values = set(tcv.taxon_id for tcv in tcvlist)
    coverage_percent = len(taxa_with_values) * 100.0 / len(taxa)

    return render_to_response('gobotany/edit_pile_character.html', {
        'there_are_any_friendly_texts': any(v.friendly_text for v in values),
        'character': character,
        'coverage_percent': coverage_percent,
        'pile': pile,
        'values': values,
        'values_json': json.dumps([value.value_str for value in values]),
        'vectors_json': json.dumps(vectors),
        }, context_instance=RequestContext(request))

def character_value_key(cv):
    """Return a sort key that puts 'NA' last."""

    if cv.value_str == 'NA':
        return 'zzzz'
    return cv.value_str
