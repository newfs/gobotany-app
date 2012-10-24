# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from gobotany.core import botany
from gobotany.core.models import (
    CopyrightHolder, Family
    )

def _images_with_copyright_holders(images):
    # Reduce a live query object to a list to only run it once.
    if not isinstance(images, list):
        images = images.select_related('image_type').all()

    # Get the copyright holders for this set of images.
    codes = set(image.creator for image in images)
    chdict = {ch.coded_name: ch for ch
              in CopyrightHolder.objects.filter(coded_name__in=codes)}

    for image in images:
        # Grab each image's "scientific name" - or whatever string is
        # preceded by a ":" at the start of its alt text!

        image.scientific_name = (image.alt or '').split(':', 1)[0]

        # Associate each image with its copyright holder, adding the
        # copyright holder information as extra attributes.

        copyright_holder = chdict.get(image.creator)
        if not copyright_holder:
            continue
        image.copyright_holder_name = copyright_holder.expanded_name
        image.copyright = copyright_holder.copyright
        image.source = copyright_holder.source

    return images

def family_view(request, family_slug):

    family_name = family_slug.capitalize()
    family = get_object_or_404(Family, name=family_name)

    # If it is decided that common names will not be required, change the
    # default below to None so the template will omit the name if missing.
    DEFAULT_COMMON_NAME = 'common name here'
    common_name = family.common_name or DEFAULT_COMMON_NAME

    family_drawings = (family.images.filter(
                       image_type__name='example drawing'))
    if not family_drawings:
        # No example drawings for this family were specified. Including
        # drawings here was planned early on but not finished for the
        # initial release. In the meantime, the first two species
        # images from the family are shown.
        species = family.taxa.all()
        for s in species:
            species_images = botany.species_images(s)
            if len(species_images) > 1:
                family_drawings = species_images[0:2]
                break
    family_drawings = _images_with_copyright_holders(family_drawings)

    pile = family.taxa.all()[0].piles.all()[0]
    pilegroup = pile.pilegroup

    return render_to_response('gobotany/family.html', {
           'family': family,
           'common_name': common_name,
           'family_drawings': family_drawings,
           'pilegroup': pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))
