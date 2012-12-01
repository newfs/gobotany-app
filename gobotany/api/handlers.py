from operator import itemgetter

from piston.handler import BaseHandler
from piston.utils import rc

from gobotany.core import botany, models

from .views import _jsonify_character

def _taxon_image(image):
    if image:
        return {'url': image.image.url,
                'type': image.image_type.name,
                'rank': image.rank,
                'title': image.alt,
                'description': image.description,
                'thumb_url': image.thumb_small(),
                'large_thumb_url': image.thumb_large(),
                }
    return ''

def _simple_taxon(taxon):
    res = {}

    first_common_name = '';
    common_names = taxon.common_names.all()
    if (common_names):
        first_common_name = common_names[0].common_name

    res['scientific_name'] = taxon.scientific_name
    res['common_name'] = first_common_name
    res['genus'] = taxon.scientific_name.split()[0] # faster than .genus.name
    res['family'] = taxon.family.name
    res['id'] = taxon.id
    res['taxonomic_authority'] = taxon.taxonomic_authority
    res['default_image'] = _taxon_image(taxon.get_default_image())
    res['images'] = [_taxon_image(i) for i in botany.species_images(taxon)]
    res['factoid'] = taxon.factoid
    return res

def _taxon_with_chars(taxon):
    res = _simple_taxon(taxon)
    piles = taxon.piles.all()
    res['piles'] = [pile.name for pile in piles]
    res['pile_slugs'] = [pile.slug for pile in piles]
    for cv in taxon.character_values.all():
        name = cv.character.short_name
        # Any character might have multiple values. For any that do,
        # return a list instead of a single value.
        if not res.has_key(name):
            # Add a single value the first time this name comes up.
            res[name] = cv.friendliest_text()
        else:
            # This name exists. Its value is either already a list,
            # or needs to be converted into one before adding the value.
            if not type(res[name]) == type(list()):
                new_list = [res[name]]
                res[name] = new_list
            res[name].append(cv.friendliest_text())
    return res


class TaxonQueryHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request, scientific_name=None):
        getdict = dict(request.GET.items())  # call items() to avoid lists
        kwargs = {}
        for k, v in getdict.items():
            kwargs[str(k)] = v
        try:
            species = botany.query_species(**kwargs)
        except models.Character.DoesNotExist:
            return rc.NOT_FOUND

        if not scientific_name:
            # Only return character values for single item lookup, keep the
            # result list simple
            listing = [ _simple_taxon(s) for s in species.all() ]

            return {'items': listing,
                    'label': 'scientific_name',
                    'identifier': 'scientific_name'}
        elif species.exists():
            try:
                taxon = species.filter(scientific_name=scientific_name)[0]
            except IndexError:
                # A taxon wasn't returned from the database.
                return rc.NOT_FOUND

            # Return full taxon with characters for single item query
            return _taxon_with_chars(taxon)
        return {}


class TaxonCountHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        kwargs = {}
        for k, v in request.GET.items():
            kwargs[str(k)] = v
        try:
            species = botany.query_species(**kwargs)
        except models.Character.DoesNotExist:
            return rc.NOT_FOUND

        matched = species.count()
        return {'matched': matched,
                'excluded': models.Taxon.objects.count() - matched}


class TaxonImageHandler(BaseHandler):
    methods_allowed = ('GET',)

    def read(self, request):
        kwargs = {}
        for k, v in request.GET.items():
            kwargs[str(k)] = v
        try:
            images = botany.species_images(**kwargs)
        except models.Taxon.DoesNotExist:
            return rc.NOT_FOUND

        return [_taxon_image(image) for image in images]


class CharactersHandler(BaseHandler):
    """List characters and character values across all piles."""
    methods_allowed = ('GET')

    def read(self, request):
        group_map = {}
        for character_group in models.CharacterGroup.objects.all():
            group_map[character_group.id] = {
                'name': character_group.name,
                'characters': [],
                }
        for character in models.Character.objects.all():
            group_map[character.character_group_id]['characters'].append({
                    'short_name': character.short_name,
                    'name': character.name,
                    })
        return sorted(group_map.values(), key=itemgetter('name'))


class CharacterHandler(BaseHandler):
    """Retrieve all character values for a character regardless of pile."""
    methods_allowed = ('GET')

    def read(self, request, character_short_name):
        r = {'type': '', 'list': []}
        for cv in models.CharacterValue.objects.filter(
            character__short_name=character_short_name):
            if cv.value_str:
                r['type'] = 'str'
                r['list'].append(cv.value_str)
            elif cv.value_min is not None and cv.value_max is not None:
                r['type'] = 'length'
                r['list'].append([cv.value_min, cv.value_max])
        return r


class BasePileHandler(BaseHandler):
    methods_allowed = ('GET', 'PUT', 'DELETE')
    fields = ('name', 'friendly_name', 'description', 'resource_uri',
              'youtube_id', 'key_characteristics', 'notable_exceptions',
              'question', 'hint', 'default_image')

    def read(self, request, slug):
        try:
            return self.model.objects.get(slug=slug)
        except (models.PileGroup.DoesNotExist, models.Pile.DoesNotExist):
            return rc.NOT_FOUND

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
            character__pile=pile).distinct()
        return [dict(name=group.name,
                     id=group.id) for group in groups]

    @staticmethod
    def default_filters(pile=None):
        filters = []
        default_filters = list(
            models.DefaultFilter.objects.filter(pile=pile)
            .select_related('character')
            )

        for default_filter in default_filters:
            filter = _jsonify_character(default_filter.character, pile.slug)
            filter['order'] = default_filter.order
            filters.append(filter)
        return filters

    @staticmethod
    def plant_preview_characters(pile=None):
        characters_list = []
        plant_preview_characters = list(
            models.PlantPreviewCharacter.objects.filter(pile=pile)
            .select_related('character', 'partner_site')
            )

        for preview_character in plant_preview_characters:
            character = {}
            character['character_short_name'] = \
                preview_character.character.short_name
            character['friendly_name'] = \
                preview_character.character.friendly_name
            character['order'] = preview_character.order
            partner_site = None
            if preview_character.partner_site:
                partner_site = preview_character.partner_site.short_name
            character['partner_site'] = partner_site
            character['unit'] = preview_character.character.unit
            character['value_type'] = preview_character.character.value_type
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


class CharacterValuesHandler(BaseHandler):
    methods_allowed = ('GET',)

    def _read(self, request, pile_slug, character_short_name):
        # Why pile_slug? The short name is already unique.
        character = models.Character.objects.get(
            short_name=character_short_name)

        for cv in models.CharacterValue.objects.filter(
            character=character):

            image_url = ''
            thumbnail_url = ''
            if cv.image:
                image_url = cv.image.url
                thumbnail_url = cv.image.thumbnail.absolute_url

            yield {'value': cv.value,
                   'friendly_text': cv.friendly_text,
                   'image_url': image_url,
                   'thumbnail_url': thumbnail_url}

    # Piston doesn't seem to like being returned a generator
    def read(self, request, pile_slug, character_short_name):
        try:
            return [x for x in self._read(request, pile_slug,
                                          character_short_name)]
        except (models.Pile.DoesNotExist, models.Character.DoesNotExist):
            return rc.NOT_FOUND
