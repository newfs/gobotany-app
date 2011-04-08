import json
from collections import defaultdict

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from gobotany.core import botany
from gobotany.core.models import (
    CharacterValue, ContentImage, Family, Pile, Taxon, TaxonCharacterValue,
    )

def jsonify(value):
    """Convert the value into a JSON HTTP response."""
    return HttpResponse(json.dumps(value), mimetype='application/json')

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
        'genus': taxon.scientific_name.split()[0],  # faster than .genus.name
        'family_id': taxon.family_id,
        'taxonomic_authority': taxon.taxonomic_authority,
        #'default_image': _taxon_image(taxon.get_default_image()),
        }
    # Get all rank 1 images
    # res['images'] = [
    #     _taxon_image(i) for i in botany.species_images(taxon, max_rank=1)
    #     ]

# API views.

def species(request, pile_slug):

    # Efficiently fetch the species that belong to this pile.

    species_query = Taxon.objects.raw(
        "SELECT core_taxon.*, core_family.name AS family_name"
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

def vectors_character(request, name):
    values = list(CharacterValue.objects.filter(character__short_name=name))
    tcvs = list(TaxonCharacterValue.objects.filter(character_value__in=values))
    species = defaultdict(list)
    for tcv in tcvs:
        species[tcv.character_value_id].append(tcv.taxon_id)
    return jsonify([
            {'value': v.value_str, 'species': sorted(species[v.id]) }
            for v in values
            ])

def vectors_key(request, key):
    if key != 'simple':
        raise Http404()
    ids = sorted( s.id for s in Taxon.objects.filter(simple_key=True) )
    return jsonify([{'key': 'simple', 'species': ids}])

def vectors_pile(request, slug):
    ids = sorted( s.id for s in Pile.objects.get(slug=slug).species.all() )
    return jsonify([{'pile': slug, 'species': ids}])
