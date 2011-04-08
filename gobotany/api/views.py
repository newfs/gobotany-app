import json
from collections import defaultdict

from django.http import HttpResponse, Http404
from gobotany.core.models import (
    CharacterValue, Pile, Taxon, TaxonCharacterValue,
    )

def jsonify(value):
    """Convert the value into a JSON HTTP response."""
    return HttpResponse(json.dumps(value), mimetype='application/json')

def vectors_character(request, name):
    values = list(CharacterValue.objects.filter(character__short_name=name))
    tcvs = list(TaxonCharacterValue.objects.filter(character_value__in=values))
    species = defaultdict(list)
    for tcv in tcvs:
        species[tcv.character_value_id].append(tcv.taxon_id)
    return jsonify([
            {'value': v.value_str, 'species': sorted(species[v.id]) }
            for v in values
            ])

def vectors_key(request, key):
    if key != 'simple':
        raise Http404()
    ids = sorted( s.id for s in Taxon.objects.filter(simple_key=True) )
    return jsonify([{'key': 'simple', 'species': ids}])

def vectors_pile(request, slug):
    ids = sorted( s.id for s in Pile.objects.get(slug=slug).species.all() )
    return jsonify([{'pile': slug, 'species': ids}])
