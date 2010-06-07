from gobotany import botany, models
from piston.handler import BaseHandler


def _taxon_with_chars(taxon):
    res = {}
    res['scientific_name'] = taxon.scientific_name
    res['id'] = taxon.id
    res['pile'] = taxon.pile.name
    res['taxonomic_authority'] = taxon.taxonomic_authority
    for cv in taxon.character_values.all():
        res[cv.character.short_name] = cv.value
    return res


class TaxonQueryHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request, scientific_name=None):
        kwargs = {}
        for k, v in request.GET.items():
            kwargs[str(k)] = v
        species = botany.query_species(**kwargs)
        if not scientific_name:
            listing = []
            for s in species.all():
                listing.append(_taxon_with_chars(s))
            return {'items': listing, 'label': 'scientific_name',
                    'identifier': 'scientific_name'}
        elif species.exists():
            return _taxon_with_chars(species.all()[0])
        return {}


class TaxonCountHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        kwargs = {}
        for k, v in request.GET.items():
            kwargs[str(k)] = v
        species = botany.query_species(**kwargs)
        matched = species.count()
        return {'matched': matched,
                'excluded': models.Taxon.objects.count() - matched}
