import hashlib
import inflect
import json
from collections import defaultdict
from operator import itemgetter
from urllib import urlencode

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import connection
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from django.views.decorators.http import etag
from django.views.decorators.vary import vary_on_headers

import gobotany.dkey.models as dkey_models
from gobotany.core import igdt
from gobotany.core.models import (
    Character, ContentImage,
    GlossaryTerm, PartnerSpecies, Pile,
    Family, Genus, Taxon, TaxonCharacterValue,
    )
from gobotany.core.partner import which_partner
from gobotany.core.questions import get_questions
from gobotany.mapping.map import (NewEnglandPlantDistributionMap,
                                  NorthAmericanPlantDistributionMap,
                                  UnitedStatesPlantDistributionMap)


inflector = inflect.engine()


def jsonify(value, headers=None, indent=1):
    """Convert the value into a JSON HTTP response."""
    response = HttpResponse(
        json.dumps(value, indent=indent if settings.DEBUG else None),
        mimetype='application/json; charset=utf-8',
        )
    if headers:
        for k, v in headers.items():  # set headers
            response[k] = v
    return response

# API helpers.

def _taxon_image(image):
    if image is None:
        return
    json = {
        'url': image.image.url,
        'type': image.image_type_name if hasattr(image, 'image_type_name')
                else image.image_type.name,
        'rank': image.rank,
        'title': image.alt,
        'thumb_url': image.thumb_small(),
        'large_thumb_url': image.thumb_large(),
        }
    return json

def _simple_taxon(taxon, pile_slug):
    genus_name, epithet = taxon.scientific_name.lower().split(None, 1)
    url = reverse('taxa-species', args=(genus_name, epithet))
    url += '?' + urlencode({'pile': pile_slug})
    return {
        'id': taxon.id,
        'scientific_name': taxon.scientific_name,
        'common_name': taxon.common_name,
        'genus': taxon.scientific_name.split()[0],  # faster than .genus.name
        'family': taxon.family_name,
        'taxonomic_authority': taxon.taxonomic_authority,
        'url': url,
        }

# API views.

def glossary_blob(request):
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

    Since we cannot guess which of these six meanings is intended in an
    arbitrary context (like the glossary itself), we had better restrict
    ourselves for the moment to highlighting terms which *are* unique
    across our current glossary.

    """
    glossaryterms = list(GlossaryTerm.objects.filter(highlight=True)
                         .extra(where=['CHAR_LENGTH(term) > 2']))

    definitions = {}
    for gt in glossaryterms:
        gt.plural = inflector.plural(gt.term)
        definitions[gt.term] = gt.lay_definition
        definitions[gt.plural] = gt.lay_definition

    # Calling gt.image.url is very slow, because this is Django, so we
    # only do it once; this will work fine as long as we do not start
    # putting different images in different storages.

    prefix = None

    for gt in glossaryterms:
        gt.image_path = gt.__dict__['image']
        if gt.image_path is not None and prefix is None:
            try:
                url = gt.image.url
                prefix = url[:-len(gt.image_path)]
            except ValueError:  # Image not found in storage.
                pass

    images = {}
    for gt in glossaryterms:
        if gt.image_path is None or prefix is None:
            continue
        images[gt.term] = prefix + gt.image_path
        images[gt.plural] = prefix + gt.image_path

    return jsonify({'definitions': definitions, 'images': images})

#

def hierarchy(request):
    genera = Genus.objects.select_related('family').order_by('family')
    hdict = defaultdict(list)
    for genus in genera:
        hdict[genus.family.name].append(genus.name)
    return jsonify({
        'hierarchy': [{'family_name': key, 'genus_names': value}
                      for key, value in hdict.items()],
        })

#

def _get_characters(short_names):
    """Return a list of characters with `short_names`, in that order."""
    cl = Character.objects.filter(short_name__in=short_names)
    by_short_name = dict((c.short_name, c) for c in cl)
    return [by_short_name[short_name] for short_name in short_names
            if short_name in by_short_name]

def _choose_best(pile, count, species_ids,
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

def _jsonify_character(character, pile_slug):
    return {
        'friendly_name': character.friendly_name,
        'short_name': character.short_name,
        'value_type': character.value_type,
        'unit': character.unit,
        'character_group': character.character_group.name,
        'question': character.question,
        'hint': character.hint,
        'image_url': (character.image.url if character.image else ''),
        'pile_slug': pile_slug,
        }

def piles_characters(request, pile_slug):
    """Returns a list of characters."""
    pile = get_object_or_404(Pile, slug=pile_slug)

    # First, build a list of raw character values.

    characters = []

    include_short_names = request.GET.getlist('include')
    if include_short_names:
        characters.extend(_get_characters(include_short_names))

    choose_best = int(request.GET.get('choose_best', 0))
    species_ids = request.GET.get('species_ids', '')
    species_ids = species_ids.split('_') if species_ids.strip() else ()

    if choose_best and species_ids:
        character_group_ids = set(
            int(n) for n in request.GET.getlist('character_group_id')
            )
        exclude_short_names = set(request.GET.getlist('exclude'))
        exclude_short_names.update(include_short_names)
        characters.extend(_choose_best(
                pile=pile,
                count=choose_best,
                species_ids=species_ids,
                character_group_ids=character_group_ids,
                exclude_short_names=exclude_short_names,
                ))
    elif not characters:
        characters = (Character.objects.filter(pile=pile)
                      .select_related('character_group'))

    # Turn the characters into a data structure for JSON.

    return jsonify([
        _jsonify_character(c, pile_slug) for c in characters
        ])

def questions(request, pile_slug):
    """Returns a list of questions for a plant subgroup."""
    pile = get_object_or_404(Pile, slug=pile_slug)
    questions = get_questions(request, pile)
    # Normal: return JSON
    questions_list = []
    for question in questions:
        character = Character.objects.get(short_name=question)
        questions_list.append(_jsonify_character(character, pile_slug))
    output = jsonify(questions_list)
    # Alternate: return HTML for browser testing with Django Debug Toolbar
    #output = render_to_response('questions_test.html',
    #                            {'questions': questions})
    return output

# The images that should be displayed on a particular dkey page.

extra_image_types = {
    u'Group 1': ['leaf'],
    u'Group 2': ['fruits', 'leaves'],
    u'Group 3': ['inflorescences', 'leaves'],
    u'Group 4': ['bark', 'leaves'],
    u'Group 5': ['bark', 'leaves'],
    u'Group 6': ['flowers', 'leaves'],
    u'Group 7': ['flowers', 'leaves'],
    u'Group 8': ['flowers', 'leaves'],
    u'Group 9': ['flowers', 'leaves'],
    u'Group 10': ['flowers', 'leaves'],
    }

def dkey_images(request, slug):

    if slug == 'key-to-the-families':
        return jsonify({})

    # Whether a dkey page displays groups of families, genera, or taxa,
    # we need to pull exactly one species to stand as the representative
    # for each taxon, and then grab all of the rank=1 content images for
    # those species.

    title = dkey_models.slug_to_title(slug)
    page = get_object_or_404(dkey_models.Page, title=title)

    taxa = None
    rank = None
    taxa_names = []
    for lead in page.leads.all():
        if lead.taxa_cache:
            rank, comma_list = lead.taxa_cache.split(':')
            taxa_names.extend(comma_list.split(','))
    if rank is None:
        return jsonify({})

    group_title = None

    if page.rank == 'group':
        group_title = page.title
    else:
        for ancestor in page.breadcrumb_cache.all():
            if ancestor.rank == 'group':
                group_title = ancestor.title

    image_types_allowed = ['plant form']
    image_types_allowed.extend(extra_image_types.get(group_title, ()))

    if rank == u'family':

        # See https://github.com/newfs/gobotany-app/issues/302
        # and https://github.com/newfs/gobotany-app/issues/304

        group_number = title.split()[-1] if page.rank == u'group' else u''

        cursor = connection.cursor()
        cursor.execute("""
            SELECT f.name, t.id,
              (SELECT id FROM core_taxon WHERE family_id = f.id LIMIT 1)
              FROM core_family f
              LEFT JOIN dkey_illustrativespecies i
                ON (i.group_number = %s AND f.name = i.family_name)
              LEFT JOIN core_taxon t
                ON (i.species_name = t.scientific_name)
              WHERE f.name IN %s""", (group_number, tuple(taxa_names),))

        rows = cursor.fetchall()
        family_map = {}
        for family_name, illustrative_taxon_id, random_taxon_id in rows:
            taxon_id = illustrative_taxon_id
            if taxon_id is None:
                taxon_id = random_taxon_id
            family_map[taxon_id] = family_name

        taxon_ids = family_map.keys()

    elif rank == u'genus':

        cursor = connection.cursor()
        cursor.execute("""
            SELECT
              (SELECT id FROM core_taxon WHERE genus_id = g.id LIMIT 1)
              FROM core_genus g
              WHERE g.name IN %s""", (tuple(taxa_names),))
        taxon_ids = [ id for (id,) in cursor.fetchall() ]

    elif rank == u'species':

        taxa = Taxon.objects.filter(scientific_name__in=taxa_names)
        taxon_ids = [ taxon.id for taxon in taxa ]

    else:
        return jsonify({})

    if taxa is None:
        taxa = Taxon.objects.filter(id__in=taxon_ids)

    ctype = ContentType.objects.get_for_model(Taxon)
    query = (ContentImage.objects
             .filter(content_type=ctype, object_id__in=taxon_ids, rank=1)
             .filter(image_type__name__in=image_types_allowed)
             .select_related('image_type')
             )

    image_map = {
        (image.object_id, image.image_type.name): image.thumb_small()
        for image in query
        }

    image_types = sorted(set(key[1] for key in image_map))
    image_lists = []

    for taxon in taxa:

        if rank == u'family':
            name = family_map[taxon.id]
            title = u'{}<br><i>({})</i>'.format(name, taxon.scientific_name)
        else:
            if rank == u'genus':
                name = taxon.genus_name()
            else:
                name = taxon.scientific_name
            title = u'<i>{}</i>'.format(taxon.scientific_name)

        image_list = []
        for image_type in image_types:
            image = image_map.get((taxon.id, image_type))
            if image is not None:
                image_list.append({
                    'image_type': image_type,
                    'image_url': image_map.get((taxon.id, image_type)),
                    })

        image_lists.append({
            'name': name,
            'scientific_name': taxon.scientific_name,
            'title': title,
            'image_list': image_list,
            })

    image_lists.sort(key=itemgetter('title'))

    return jsonify({
            'image_types': image_types,
            'image_lists': image_lists,
            })

# Higher-order taxa.

def family(request, family_slug):
    family = get_object_or_404(Family, name=family_slug.capitalize())
    ttype = ContentType.objects.get_for_model(Taxon)

    # Keep only one taxon per genus as its representative image.

    taxa = list(family.taxa.order_by('scientific_name'))

    one_taxa_per_genus = [taxa[0]]
    for i in range(1, len(taxa)):
        if taxa[i - 1].genus_id != taxa[i].genus_id:
            one_taxa_per_genus.append(taxa[i])

    ids = { taxon.id for taxon in one_taxa_per_genus }

    # Since the import code only creates a single rank=1 image for each
    # (taxa + image_type) combination, we can filter on rank=1 and know
    # that we are getting at most one image of each species regardless
    # of the image_type that the user selects to view.

    images = [
        _taxon_image(image) for image in ContentImage.objects
            .select_related('image_type')
            .filter(content_type=ttype, object_id__in=ids, rank=1)
        ]

    drawings = family.images.all() # TODO: filter image_type 'example drawing'

    return jsonify({
        'name': family.name,
        'images': images,
        'drawings': list(drawings),
        })

def genus(request, genus_slug):
    genus = get_object_or_404(Genus, name=genus_slug.capitalize())

    ttype = ContentType.objects.get_for_model(Taxon)
    ids = { taxon.id for taxon in genus.taxa.all() }

    # Since the import code only creates a single rank=1 image for each
    # (taxa + image_type) combination, we can filter on rank=1 and know
    # that we are getting at most one image of each species regardless
    # of the image_type that the user selects to view.

    images = [
        _taxon_image(image) for image in ContentImage.objects
            .select_related('image_type')
            .filter(content_type=ttype, object_id__in=ids, rank=1)
        ]

    drawings = genus.images.all() # TODO: filter image_type 'example drawing'

    return jsonify({
        'name': genus.name,
        'images': images,
        'drawings': list(drawings),
        })

# Lower-order taxa.

_species_cache = {}

def species(request, pile_slug):

    # Pull the result from our hard cache, if available.

    # TODO: fix. Disabled when upgrading to Django 1.5 due to error in
    # Chrome when pulling from the cache:
    # Error 354 (net::ERR_CONTENT_LENGTH_MISMATCH): The server unexpectedly
    # closed the connection.
    # Somehow the cached response has a much shorter Content-Length than the
    # original response.
    #
    #if pile_slug in _species_cache:
    #    return _species_cache[pile_slug]

    # Efficiently fetch the species that belong to this pile.  (Common
    # name is selected nondeterministically because, frankly, the data
    # model gives us no other choice if a plant has more than one common
    # name listed in the database.)

    species_query = Taxon.objects.raw(
        "SELECT core_taxon.*, core_family.name AS family_name,"
        " (SELECT common_name FROM core_commonname"
        "  WHERE core_commonname.taxon_id = core_taxon.id"
        "  LIMIT 1)"
        "  AS common_name"
        " FROM core_taxon"
        " JOIN core_family ON (core_taxon.family_id = core_family.id)"
        " JOIN core_pile_species ON (taxon_id = core_taxon.id)"
        " JOIN core_pile ON (pile_id = core_pile.id)"
        " WHERE core_pile.slug = %s",
        (pile_slug,))

    species_list = list(species_query)

    # Efficiently fetch the images that belong to these taxa.

    image_query = ContentImage.objects.raw(
        "SELECT core_contentimage.*, core_imagetype.name AS image_type_name"
        " FROM core_contentimage"
        " JOIN core_imagetype"
        "  ON (core_contentimage.image_type_id = core_imagetype.id)"
        " JOIN django_content_type"
        "  ON (core_contentimage.content_type_id =django_content_type.id)"
        " WHERE core_contentimage.rank <= 1"
        "  AND core_contentimage.object_id IN %s"
        "  AND django_content_type.app_label = 'core'"
        "  AND django_content_type.model = 'taxon'",
        (tuple( species.id for species in species_list ),))

    image_dict = defaultdict(list)  # taxon_id -> [ContentImage, ...]
    for image in image_query:
        image_dict[image.object_id].append(image)

    del species_query  # beware of leaving object references around
    del image_query

    # Build and return our response.

    result = []
    while species_list:
        species = species_list.pop()  # pop() to free memory as we go
        d = _simple_taxon(species, pile_slug)
        d['images'] = images = []
        image_list = image_dict.pop(species.id, ())
        for image in image_list:
            images.append(_taxon_image(image))
        result.append(d)

    # Hard-cache the result, since our species lists do not currently
    # change during the day in production.

    _species_cache[pile_slug] = jsonify(result)
    return _species_cache[pile_slug]

#

def vectors_character(request, name):
    character = get_object_or_404(Character, short_name=name)
    mm = character.UNIT_MM.get(character.unit)
    if mm is None:
        mm = 1.0
    values = character.character_values.all()
    tcvs = list(TaxonCharacterValue.objects.filter(character_value__in=values))
    species = defaultdict(list)
    for tcv in tcvs:
        species[tcv.character_value_id].append(tcv.taxon_id)
    return jsonify([{
        'friendly_text': v.friendly_text,
        'taxa': sorted(species[v.id]),
        'choice': v.value_str,
        'scalar': v.value_flt,
        'min': v.value_min and v.value_min * mm,
        'max': v.value_max and v.value_max * mm,
        #
        'image_url': v.image.url if v.image else '',
        } for v in values ])

@cache_page(0)
@vary_on_headers('Host')
def vectors_key(request, key):
    if key != 'simple':
        raise Http404()
    partner = which_partner(request)
    ids = sorted( ps.species_id for ps in PartnerSpecies.objects
                  .filter(partner=partner, simple_key=True) )
    return jsonify([{'key': 'simple', 'species': ids}],
                   headers={'Expires': 'Thu, 1 Jan 1970 00:00:00 GMT'})

def vectors_pile(request, slug):
    pile = get_object_or_404(Pile, slug=slug)
    ids = sorted( s.id for s in pile.species.all() )
    return jsonify([{'pile': slug, 'species': ids}])


# Big vector
#
# What design?
#
# [...
#  {name: 'habitat',
#   type: 'string',
#   values: [...
#            [5, 8, 9],  <-- one array of taxon IDs per value
#            ...

def pile_vector_set(request, slug):

    pile = get_object_or_404(Pile, slug=slug)

    # These four queries are the barest minimum required to learn how
    # many character values each character has, and what species belong
    # to each value, which together is all the information that the
    # front-end needs to display character and rank them by their
    # usefulness.
    #
    # And, yes, using Django ORM objects here unfortunately destroys
    # performance, as does trying to combine these queries into a single
    # JOIN that repeats redundant data.
    #
    # 1.

    cursor = connection.cursor()

    cursor.execute("""

      SELECT cg.id, cg.name
        FROM core_charactergroup cg

      """, [pile.id])

    character_group_map = {}
    for cgid, name in cursor.fetchall():
        character_group_map[cgid] = name

    # 2.

    cursor = connection.cursor()

    cursor.execute("""

      SELECT c.id, c.short_name, c.friendly_name, c.character_group_id,
          c.ease_of_observability, c.value_type
        FROM core_character c
        WHERE c.pile_id = %s

      """, [pile.id])

    character_map = {}
    for cid, short_name, name, cgid, ease, value_type in cursor.fetchall():
        character_map[cid] = {
            'slug': short_name,
            'name': name,
            'group_name': character_group_map[cgid],
            'ease': ease,
            'type': value_type,
            'values': [],
            }

    # 3.

    cursor.execute("""

      SELECT c.id, cv.id
        FROM core_character c
        JOIN core_charactervalue cv ON (c.id = cv.character_id)
        WHERE c.pile_id = %s

      """, [pile.id])

    character_value_map = {}
    for cid, cvid in cursor.fetchall():
        taxonid_list = []  # to be filled in below!
        character_value_map[cvid] = taxonid_list
        character_map[cid]['values'].append(taxonid_list)

    # 4.

    cursor.execute("""

      SELECT cv.id, taxon_id
        FROM core_character c
        JOIN core_charactervalue cv ON (c.id = cv.character_id)
        JOIN core_taxoncharactervalue tcv ON (cv.id = tcv.character_value_id)
        WHERE c.pile_id = %s

      """, [pile.id])

    for cvid, taxonid in cursor.fetchall():
        character_value_map[cvid].append(taxonid)

    # If you want to gander at the SQL times with the debug toolbar:
    # from django.http import HttpResponse
    # return HttpResponse('<html><head></head><body>foo</body>')

    return jsonify(character_map.values(), indent=False)

# Plant distribution maps

def _shade_map(distribution_map,  genus, epithet):
    scientific_name = ' '.join([genus.title(), epithet.lower()])
    distribution_map.set_plant(scientific_name)
    return distribution_map.shade()

def _compute_map_etag(request, distribution_map, genus, epithet):
    """Generate an ETag for allowing caching of maps. This requires
    shading the map upon every request, but saves much bandwidth.
    """
    shaded_map = _shade_map(distribution_map, genus, epithet)
    h = hashlib.md5()
    h.update(shaded_map.tostring())
    return h.hexdigest()

@etag(_compute_map_etag)
def _distribution_map(request, distribution_map, genus, epithet):

    # BONAP gives one species a different name than FNA; as a temporary
    # measure, we rename the species here.  A more permament solution
    # (whether a data fix, or a table to drive renaming) will be
    # discussed here:
    #
    # https://github.com/newfs/gobotany-app/issues/277

    if (genus, epithet) == ('berberis', 'aquifolium'):
        genus, epithet = 'mahonia', 'aquifolium'

    shaded_map = _shade_map(distribution_map, genus, epithet)
    return HttpResponse(shaded_map.tostring(), mimetype='image/svg+xml')

def new_england_distribution_map(request, genus, epithet):
    """Return a vector map of New England showing county-level
    distribution data for a plant.
    """
    distribution_map = NewEnglandPlantDistributionMap()
    return _distribution_map(request, distribution_map, genus, epithet)

def united_states_distribution_map(request, genus, epithet):
    """Return a vector map of the United States showing county-level
    distribution data for a plant.
    """
    distribution_map = UnitedStatesPlantDistributionMap()
    return _distribution_map(request, distribution_map, genus, epithet)

def north_american_distribution_map(request, genus, epithet):
    """Return a vector map of North America showing county-level
    distribution data for a plant.
    """
    distribution_map = NorthAmericanPlantDistributionMap()
    return _distribution_map(request, distribution_map, genus, epithet)
