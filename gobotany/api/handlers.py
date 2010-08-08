from gobotany.core import botany, models
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
    res['piles'] = taxon.get_piles()

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
            listing = [ _taxon_with_chars(s) for s in species.all() ]
            return {'items': listing, 'label': 'scientific_name',
                    'identifier': 'scientific_name'}
        elif species.exists():
            taxon = species.filter(scientific_name=scientific_name)[0]
            return _taxon_with_chars(taxon)
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
    fields = ('name', 'friendly_name', 'description', 'resource_uri',
              'youtube_id', 'key_characteristics', 'notable_exceptions',
              'default_image')

    def read(self, request, slug):
        return self.model.objects.get(slug=slug)

    def update(self, request, slug):
        obj = self.model.objects.get(slug=slug)
        for k, v in request.PUT.items():
            if k in self.fields:
                setattr(obj, k, v)
        obj.save()
        return obj

    def delete(self, request, slug):
        obj = self.model.objects.get(slug=slug)
        obj.delete()
        return rc.DELETED

    @staticmethod
    def default_image(pile=None):
        if pile is not None:
            return _taxon_image(pile.get_default_image())


class FakeDefaultFilter(object):
    pass


class PileHandler(BasePileHandler):
    model = models.Pile
    fields = BasePileHandler.fields + ('default_filters',)

    @staticmethod
    def resource_uri(pile=None):
        return 'api-pile', ['slug' if pile is None else pile.id]

    @staticmethod
    def default_filters(pile=None):
        filters = []
        default_filters = list(
            models.DefaultFilter.objects.filter(pile=pile)
            )

        # -- START --
        # Remove this when filters can be interactively selected; for
        # now, this adds in LENGTH filters to exercise the UI.  (And
        # remove the FakeDefaultFilter defined above, too!)
        characters = models.Character.objects.filter(
            value_type=u'LENGTH',
            character_values__pile=pile,
            )
        print len(characters)
        order = max(
            default_filter.order for default_filter in default_filters
            ) + 1
        for character in characters:
            fake_default_filter = FakeDefaultFilter()
            fake_default_filter.character = character
            order += 1
            fake_default_filter.order = order
            default_filters.append(fake_default_filter)
            if order > 6:
                break  # don't get carried away
        # -- END --

        for default_filter in default_filters:
            filter = {}
            filter['character_short_name'] = \
                default_filter.character.short_name
            filter['character_friendly_name'] = \
                default_filter.character.friendly_name
            filter['order'] = default_filter.order
            filter['value_type'] = default_filter.character.value_type
            filters.append(filter)
        return filters


class PileGroupHandler(BasePileHandler):
    model = models.PileGroup

    @staticmethod
    def resource_uri(pilegroup=None):
        return 'api-pilegroup', ['slug' if pilegroup is None else pilegroup.id]


class PileListingHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        lst = [x for x in models.Pile.objects.all()]
        return {'items': lst}


class PileGroupListingHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        lst = [x for x in models.PileGroup.objects.all()]
        return {'items': lst}


class CharacterValuesHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request, pile_slug, character_short_name):
        pile = models.Pile.objects.get(slug=pile_slug)
        character = models.Character.objects.get(
            short_name=character_short_name)
        return models.CharacterValue.objects.filter(pile=pile, 
                                                    character=character)
