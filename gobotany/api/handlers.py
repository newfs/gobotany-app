from gobotany.core import botany, models
from piston.handler import BaseHandler
from piston.utils import rc


def _taxon_image(image):
    if image:
        img = image.image
        return {'url': img.url,
                'type': image.image_type.name,
                'rank': image.rank,
                'title': image.alt,
                'description': image.description,
                'thumb_url': img.thumbnail.absolute_url,
                'thumb_width': img.thumbnail.width(),
                'thumb_height': img.thumbnail.height(),
                'scaled_url': img.extra_thumbnails['large'].absolute_url,
                'scaled_width': img.extra_thumbnails['large'].width(),
                'scaled_height': img.extra_thumbnails['large'].height(),
                }
    return ''

def _simple_taxon(taxon):
    res = {}
    res['scientific_name'] = taxon.scientific_name
    res['id'] = taxon.id
    res['taxonomic_authority'] = taxon.taxonomic_authority
    res['default_image'] = _taxon_image(taxon.get_default_image())
    # Get all rank 1 images
    res['images'] = [_taxon_image(i) for i in botany.species_images(taxon,
                                                                    max_rank=1)]
    return res

def _taxon_with_chars(taxon):
    res = _simple_taxon(taxon)
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
            # Only return character values for single item lookup, keep the
            # result list simple
            listing = [ _simple_taxon(s) for s in species.all() ]
            return {'items': listing, 'label': 'scientific_name',
                    'identifier': 'scientific_name'}
        elif species.exists():
            taxon = species.filter(scientific_name=scientific_name)[0]
            # Return full taxon with characters for single item query
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
    fields = BasePileHandler.fields + ('character_groups', 'default_filters',
                                       'plant_preview_characters')

    @staticmethod
    def resource_uri(pile=None):
        return 'api-pile', ['slug' if pile is None else pile.id]

    @staticmethod
    def character_groups(pile=None):
        groups = models.CharacterGroup.objects.filter(
            character__character_values__pile=pile
            ).distinct()
        return [ dict(name=group.name) for group in groups ]

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
        order = (default_filters and max(
            default_filter.order for default_filter in default_filters
            ) or 0) + 1
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
            filter['notable_exceptions'] = getattr(default_filter,
                                                   'notable_exceptions', u'')
            filter['key_characteristics'] = getattr(default_filter,
                                                    'key_characteristics', u'')
            filters.append(filter)
        return filters

    @staticmethod
    def plant_preview_characters(pile=None):
        characters_list = []
        plant_preview_characters = list(
            models.PlantPreviewCharacter.objects.filter(pile=pile))

        for preview_character in plant_preview_characters:
            character = {}
            character['character_short_name'] = \
                preview_character.character.short_name
            character['character_friendly_name'] = \
                preview_character.character.friendly_name
            character['order'] = preview_character.order
            characters_list.append(character)
        return characters_list


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


class CharacterListingHandler(BaseHandler):
    methods_allowed = ('GET',)
    
    def read(self, request, pile_slug):
        # temporary: dummy characters and groups
        characters = \
            [ {'group_name': 'char_group1',
               'characters': [ {'character_friendly_name': 'fname1',
                                'character_short_name': 'sname1',
                                'value_type': 'TEXT'},
                               {'character_friendly_name': 'fname2',
                                'character_short_name': 'sname2',
                                'value_type': 'TEXT'},
                               {'character_friendly_name': 'fname3',
                                'character_short_name': 'sname3',
                                'value_type': 'TEXT'} ] },
              {'group_name': 'char_group2',
               'characters': [ {'character_friendly_name': 'fname4',
                                'character_short_name': 'sname4',
                                'value_type': 'TEXT'},
                               {'character_friendly_name': 'fname5',
                                'character_short_name': 'sname5',
                                'value_type': 'TEXT'},
                               {'character_friendly_name': 'fname6',
                                'character_short_name': 'sname6',
                                'value_type': 'TEXT'} ] },
              {'group_name': 'char_group3',
               'characters': [ {'character_friendly_name': 'fname7',
                                'character_short_name': 'sname7',
                                'value_type': 'TEXT'},
                               {'character_friendly_name': 'fname8',
                                'character_short_name': 'sname8',
                                'value_type': 'TEXT'},
                               {'character_friendly_name': 'fname9',
                                'character_short_name': 'sname9',
                                'value_type': 'TEXT'} ]
              } ]
        return characters


class CharacterValuesHandler(BaseHandler):
    methods_allowed = ('GET',)

    def _read(self, request, pile_slug, character_short_name):
        pile = models.Pile.objects.get(slug=pile_slug)
        character = models.Character.objects.get(
            short_name=character_short_name)

        for cv in models.CharacterValue.objects.filter(
            pile=pile, character=character):

            species = models.Taxon.objects.filter(character_values=cv)
            count = species.count()
            if count > 0:
                yield {'value': cv.value, 'count': count}

    # Piston doesn't seem to like being returned a generator
    def read(self, request, pile_slug, character_short_name):
        return [x for x in self._read(request, pile_slug,
                                      character_short_name)]
