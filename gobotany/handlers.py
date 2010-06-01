from gobotany import botany
from piston.handler import BaseHandler


def serialize(obj):
    return obj.__dict__


class TaxonQueryHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        kwargs = {}
        for k, v in request.GET.items():
            kwargs[k] = v
        species = botany.query_species(**kwargs)
        listing = []
        for s in species:
            res = {}
            res['scientific_name'] = s.scientific_name
            res['id'] = s.id
            res['pile'] = s.pile.name
            for cv in s.character_values.all():
                res[cv.character.short_name] = cv.value
            listing.append(res)
        return listing


class TaxonHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request, scientific_name=None):
        species = botany.query_species(scientific_name=scientific_name)
        if len(species) > 0:
            res = {}
            s = species[0]
            res['scientific_name'] = s.scientific_name
            res['id'] = s.id
            res['pile'] = s.pile.name
            for cv in s.character_values.all():
                res[cv.character.short_name] = cv.value
            return res
        return {}
