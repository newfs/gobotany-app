import json
from collections import defaultdict

from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page
from gobotany.core.models import (
    CharacterValue, ContentImage, GlossaryTerm, Pile,
    Taxon, TaxonCharacterValue,
    )

def jsonify(value):
    """Convert the value into a JSON HTTP response."""
    return HttpResponse(
        json.dumps(value, indent=1 if settings.DEBUG else None),
        mimetype='application/json',
        )

# API helpers.

def _taxon_image(image):
    if image is None:
        return
    img = image.image
    large = img.extra_thumbnails['large']
    return {
        'url': img.url,
        'type': image.image_type_name,
        'rank': image.rank,
        'title': image.alt,
        'description': image.description,
        'thumb_url': img.thumbnail.absolute_url,
        'thumb_width': img.thumbnail.width(),
        'thumb_height': img.thumbnail.height(),
        'scaled_url': large.absolute_url,
        'scaled_width': large.width(),
        'scaled_height': large.height(),
        }

def _simple_taxon(taxon):
    return {
        'id': taxon.id,
        'scientific_name': taxon.scientific_name,
        'common_name': taxon.common_name,
        'genus': taxon.scientific_name.split()[0],  # faster than .genus.name
        'family': taxon.family_name,
        'taxonomic_authority': taxon.taxonomic_authority,
        }

# API views.

@cache_page(20 * 60)
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
    terms = {}
    discards = set()
    for g in GlossaryTerm.objects.all():
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
    return jsonify(terms)

@cache_page(20 * 60)
def species(request, pile_slug):

    # Efficiently fetch the species that belong to this pile.  (Common
    # name is selected nondeterministically because, frankly, the data
    # model gives us no other choice if a plant has more than one common
    # name listed in the database.)

    species_query = Taxon.objects.raw(
        "SELECT core_taxon.*, core_family.name AS family_name,"
        " (SELECT common_name FROM core_commonname JOIN core_taxon_common_names"
        "  ON (core_commonname.id = core_taxon_common_names.commonname_id)"
        "  WHERE core_taxon_common_names.taxon_id = core_taxon.id"
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

    # Build and return our response.

    result = []
    for species in species_list:
        d = _simple_taxon(species)
        d['images'] = images = []
        for image in image_dict[species.id]:
            images.append(_taxon_image(image))
        result.append(d)

    return jsonify(result)

#

@cache_page(20 * 60)
def vectors_character(request, name):
    values = list(CharacterValue.objects.filter(character__short_name=name))
    tcvs = list(TaxonCharacterValue.objects.filter(character_value__in=values))
    species = defaultdict(list)
    for tcv in tcvs:
        species[tcv.character_value_id].append(tcv.taxon_id)
    return jsonify([{
        'friendly_text': v.friendly_text,
        'key_characteristics': v.key_characteristics,
        'notable_exceptions': v.notable_exceptions,
        'species': sorted(species[v.id]),
        'choice': v.value_str,
        'scalar': v.value_flt,
        'min': v.value_min,
        'max': v.value_max,
        #
        'thumbnail_url': v.image.thumbnail.absolute_url if v.image else '',
        'image_url': v.image.url if v.image else '',
        } for v in values ])

@cache_page(20 * 60)
def vectors_key(request, key):
    if key != 'simple':
        raise Http404()
    ids = sorted( s.id for s in Taxon.objects.filter(simple_key=True) )
    return jsonify([{'key': 'simple', 'species': ids}])

@cache_page(20 * 60)
def vectors_pile(request, slug):
    pile = get_object_or_404(Pile, slug=slug)
    ids = sorted( s.id for s in pile.species.all() )
    return jsonify([{'pile': slug, 'species': ids}])
