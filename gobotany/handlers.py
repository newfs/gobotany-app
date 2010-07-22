from gobotany import botany, models
from piston.handler import BaseHandler
from piston.utils import rc


def _taxon_image(image):
    if image:
        return {'url': image.image.url,
                'type': image.image_type.name,
                'rank': image.rank,
                'title': image.alt,
                'description': image.description}
    return ''


def _taxon_with_chars(taxon):
    res = {}
    res['scientific_name'] = taxon.scientific_name
    res['id'] = taxon.id
    res['taxonomic_authority'] = taxon.taxonomic_authority
    res['default_image'] = _taxon_image(taxon.get_default_image())

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


class TaxonImageHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        kwargs = {}
        for k, v in request.GET.items():
            kwargs[str(k)] = v
        images = botany.species_images(**kwargs)
        return [_taxon_image(image) for image in images]


class BasePileHandler(BaseHandler):
    methods_allowed = ('GET', 'PUT', 'DELETE')
    fields = ('name', 'friendly_name', 'description')

    def read(self, request, name):
        return self.model.objects.get(name=name)

    def update(self, request, name):
        obj = self.model.objects.get(name=name)
        for k, v in request.PUT.items():
            if k in self.fields:
                setattr(obj, k, v)
        obj.save()
        return obj

    def delete(self, request, name):
        obj = self.model.objects.get(name=name)
        obj.delete()
        return rc.DELETED


class PileHandler(BasePileHandler):
    model = models.Pile


class PileGroupHandler(BasePileHandler):
    model = models.PileGroup


class BasePileListingHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        lst = [{'name': x.name} for x in self.model.objects.all()]
        return {'items': lst}


class PileListingHandler(BasePileListingHandler):
    model = models.Pile


class PileGroupListingHandler(BasePileListingHandler):
    model = models.PileGroup
