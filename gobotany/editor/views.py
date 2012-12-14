from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from gobotany.core import models

def e404(request):
    raise Http404()

@permission_required('botanist')
def piles_view(request):
    piles = models.Pile.objects.all()
    return render_to_response('gobotany/edit_piles.html', {
        'piles' : piles,
        }, context_instance=RequestContext(request))

@permission_required('botanist')
def pile_view(request, pile_slug):
    pile = get_object_or_404(models.Pile, slug=pile_slug)
    return render_to_response('gobotany/edit_pile.html', {
        'pile' : pile,
        }, context_instance=RequestContext(request))

@permission_required('botanist')
def edit_pile_character(request, pile_slug, character_slug):
    pile = get_object_or_404(models.Pile, slug=pile_slug)
    character = get_object_or_404(models.Character, short_name=character_slug)

    taxa = list(pile.species.all())
    values = list(character.character_values.all())

    checked_boxes = set(
        (tcv.taxon_id, tcv.character_value_id) for tcv
        in models.TaxonCharacterValue.objects.filter(
            taxon__in=taxa, character_value__in=values)
        )

    def big_loop():
        for taxon in taxa:
            boxes = [(value, (taxon.id, value.id) in checked_boxes)
                     for value in values]
            yield taxon, boxes

    return render_to_response('gobotany/edit_pile_character.html', {
        'are_there_any_friendly_texts': any(v.friendly_text for v in values),
        'big_loop': big_loop,
        'character': character,
        'pile': pile,
        'taxa': taxa,
        'values': values,
        }, context_instance=RequestContext(request))
