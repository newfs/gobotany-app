import json
from collections import defaultdict

from django.http import HttpResponse
from gobotany.core.models import Character, CharacterValue, \
    TaxonCharacterValue

def jsonify(value):
    """Convert the value into a JSON HTTP response."""
    return HttpResponse(json.dumps(value), mimetype='application/json')

def vector_character(request, name):
    values = list(CharacterValue.objects.filter(character__short_name=name))
    tcvs = list(TaxonCharacterValue.objects.filter(character_value__in=values))
    species = defaultdict(list)
    for tcv in tcvs:
        species[tcv.character_value_id].append(tcv.taxon_id)
    return jsonify([
            {'value': v.value_str, 'species': sorted(species[v.id]) }
            for v in values ])
