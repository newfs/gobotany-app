from django.shortcuts import get_object_or_404
from gobotany.core import botany, igdt, models
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
    res['genus'] = taxon.scientific_name.split()[0] # faster than .genus.name
    res['family'] = taxon.family.name
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
    
    def _get_character_value_counts(self, character_names, **kwargs):
        value_counts = []
        if character_names:
            for character_name in character_names:
                counts = {}
                pile = models.Pile.objects.get(slug=kwargs['pile'])
                try:
                    character = models.Character.objects.get(
                        short_name=character_name)
                except models.Character.DoesNotExist:
                    # Ignore any characters that don't exist in the database.
                    continue
                if character.value_type == 'TEXT':
                    for cv in models.CharacterValue.objects.filter(
                              pile=pile, character=character):
                        # Get the species with the current query, setting this
                        # character value as a 'hypothetical' one in order to
                        # elicit the desired count.
                        temp_kwargs = dict(kwargs)
                        temp_kwargs[character_name.encode()] = cv.value
                        species = botany.query_species(**temp_kwargs)
                        counts[cv.value] = species.count()
                value_counts.append({'name': character_name, 
                                     'counts': counts})
        return value_counts


    def read(self, request, scientific_name=None):
        kwargs = {}
        for k, v in request.GET.items():
            kwargs[str(k)] = v
        try:
            species = botany.query_species(**kwargs)
        except models.Character.DoesNotExist:
            return rc.NOT_FOUND

        if not scientific_name:
            # Only return character values for single item lookup, keep the
            # result list simple
            listing = [ _simple_taxon(s) for s in species.all() ]

            # Add value counts for each character requested.
            value_counts = [];
            counts_for = request.GET.get('_counts_for')
            if counts_for:
                character_names = counts_for.split(',')
                value_counts = self._get_character_value_counts(
                    character_names, **kwargs)

            return {'items': listing,
                    'value_counts': value_counts,
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


class BasePileHandler(BaseHandler):
    methods_allowed = ('GET', 'PUT', 'DELETE')
    fields = ('name', 'friendly_name', 'description', 'resource_uri',
              'youtube_id', 'key_characteristics', 'notable_exceptions',
              'default_image')

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
            character__character_values__pile=pile).distinct()
        return [dict(name=group.name,
                     id=group.id) for group in groups]

    @staticmethod
    def default_filters(pile=None):
        filters = []
        default_filters = list(
            models.DefaultFilter.objects.filter(pile=pile)
            )

        for default_filter in default_filters:
            filter = {}
            filter['character_short_name'] = \
                default_filter.character.short_name
            filter['character_friendly_name'] = \
                default_filter.character.friendly_name
            filter['order'] = default_filter.order
            filter['value_type'] = default_filter.character.value_type
            filter['unit'] = default_filter.character.unit
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

    def _get_characters(self, short_names):
        """Return a list of characters with `short_names`, in that order."""
        cl = models.Character.objects.filter(short_name__in=short_names)
        by_short_name = dict( (c.short_name, c) for c in cl )
        return [ by_short_name[short_name] for short_name in short_names ]

    def _choose_best(self, pile, count, species_ids,
                     character_group_ids, exclude_short_names):
        """Return a list of characters, best first, for these species.

        `count` - how many characters to return.
        `species_ids` - the species you want to distinguish.
        `character_groups` - if non-empty, only characters from these groups.
        `exclude_short_names` - characters to exclude from the list.

        """
        result = igdt.rank_characters(pile, species_ids)
        characters = []
        for score, entropy, coverage, character in result:
            # There are several reasons we might disqualify a character.

            if character.value_type not in (u'TEXT', u'LENGTH'):
                continue
            if character.short_name in exclude_short_names:
                continue
            if character_group_ids and (character.character_group_id
                                        not in character_group_ids):
                continue

            # Otherwise, keep this character!

            characters.append(character)
            if len(characters) == count:
                break

        return characters

    def _jsonify_character(self, character):
        return {
            'friendly_name': character.friendly_name,
            'short_name': character.short_name,
            'value_type': character.value_type,
            'unit': character.unit,
            'characteracter_group': character.character_group.name,
            'key_characteristics': character.key_characteristics,
            'notable_exceptions': character.notable_exceptions,
            }

    def read(self, request, pile_slug):
        """Returns a list of characters."""

        piles = models.Pile.objects.filter(slug=pile_slug).all()
        if not piles:
            return rc.NOT_FOUND
        pile = piles[0]

        # First, build a list of raw character values.

        characters = []

        include_short_names = request.GET.getlist('include')
        if include_short_names:
            characters.extend(self._get_characters(include_short_names))

        choose_best = int(request.GET.get('choose_best', 0))
        species_ids = request.GET.getlist('species_id')

        if choose_best and species_ids:
            character_group_ids = set(
                int(n) for n in request.GET.getlist('character_group_id')
                )
            exclude_short_names = set(request.GET.getlist('exclude'))
            exclude_short_names.update(include_short_names)
            characters.extend(self._choose_best(
                    pile=pile,
                    count=choose_best,
                    species_ids=species_ids,
                    character_group_ids=character_group_ids,
                    exclude_short_names=exclude_short_names,
                    ))

        # Turn the characters into a data structure for JSON.

        return [
            self._jsonify_character(c) for c in characters
            ]


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
            key_characteristics = cv.key_characteristics
            notable_exceptions = cv.notable_exceptions
            if count > 0:
                yield {'value': cv.value,
                       'count': count,
                       'key_characteristics': key_characteristics,
                       'notable_exceptions': notable_exceptions}

    # Piston doesn't seem to like being returned a generator
    def read(self, request, pile_slug, character_short_name):
        try:
            return [x for x in self._read(request, pile_slug,
                                          character_short_name)]
        except (models.Pile.DoesNotExist, models.Character.DoesNotExist):
            return rc.NOT_FOUND

class GlossaryBlobHandler(BaseHandler):
    methods_allowed = ('GET',)
    def read(self, request):
        """Return a dictionary of glossary terms and definitions.

        For now we omit glossary terms for which there are duplicates -
        like "Absent", which as of the writing of this comment has six
        definitions:

        Absent. no, spores are present throughout
        Absent. no horizontal stem
        Absent. no constrictions
        Absent. no branches
        Absent. no, all leaves on the horizontal stem are about the same size
        Absent. no stomates

        Since we cannot guess which of these six meanings is intended in
        an arbitrary context (like the glossary itself), we had better
        restrict ourselves for the moment to highlighting terms which
        *are* unique across our current glossary.

        """
        terms = {}
        discards = set()
        for g in models.GlossaryTerm.objects.all():
            term = g.term
            if len(term) < 3 or not g.lay_definition:
                pass
            elif term in discards:
                pass
            elif term in terms:
                del terms[term]
                discards.add(term)
            else:
                terms[term] = g.lay_definition
        return terms
