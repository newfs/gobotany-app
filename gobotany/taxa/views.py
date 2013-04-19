# -*- coding: utf-8 -*-

from itertools import groupby
from operator import itemgetter

from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.vary import vary_on_headers

from gobotany.core import botany
from gobotany.core.models import (
    CopyrightHolder, Family, Genus, PartnerSite, PartnerSpecies, Pile,
    PlantPreviewCharacter, Taxon
    )
from gobotany.core.partner import (which_partner, per_partner_template,
                                   render_to_response_per_partner)
from gobotany.dkey import models as dkey_models

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
        image.contact_info = copyright_holder.contact_info
        image.source = copyright_holder.source.replace(
            'http://', '').replace('University', 'U.')

    return images


@vary_on_headers('Host')
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

    return render_to_response_per_partner('family.html', {
           'family': family,
           'common_name': common_name,
           'family_drawings': family_drawings,
           'pilegroup': pilegroup,
           'pile': pile,
           }, request)


@vary_on_headers('Host')
def genus_view(request, genus_slug):

    genus_name = genus_slug.capitalize()
    genus = get_object_or_404(Genus, name=genus_name)

    # If it is decided that common names will not be required, change the
    # default below to None so the template will omit the name if missing.
    DEFAULT_COMMON_NAME = 'common name here'
    common_name = genus.common_name or DEFAULT_COMMON_NAME

    genus_drawings = genus.images.filter(image_type__name='example drawing')
    if not genus_drawings:
        # No example drawings for this genus were specified. Including
        # drawings here was planned early on but not finished for the
        # initial release. In the meantime, the first two species
        # images from the genus are shown.
        species = genus.taxa.all()
        for s in species:
            species_images = botany.species_images(s)
            if len(species_images) > 1:
                genus_drawings = species_images[0:2]
                break
    genus_drawings = _images_with_copyright_holders(genus_drawings)

    pile = genus.taxa.all()[0].piles.all()[0]
    pilegroup = pile.pilegroup

    return render_to_response_per_partner('genus.html', {
           'genus': genus,
           'common_name': common_name,
           'genus_drawings': genus_drawings,
           'pilegroup': pilegroup,
           'pile': pile,
           }, request)


def _native_to_north_america_status(taxon):
    native_to_north_america = ''
    if taxon.north_american_native == True:
        native_to_north_america = 'Yes'
        if taxon.north_american_introduced == True:
            # This is for plants that are native to N. America but are
            # also native elsewhere or have introduced varieties.
            native_to_north_america += ' and no (some introduced)'
    elif taxon.north_american_native == False:
        native_to_north_america = 'No'
    return native_to_north_america


def _format_character_value(character_value):
    """Render a character value for display."""
    if character_value:
        character = character_value.character
        if character.value_type == 'TEXT':
            return (character_value.friendly_text or
                    character_value.value_str or u'')
        else:
            NUM_FORMAT = u'%.9g'
            vmin = character_value.value_min
            vmax = character_value.value_max

            if vmin is not None:
                vmin = NUM_FORMAT % vmin
            if vmax is not None:
                vmax = NUM_FORMAT % vmax

            if vmin is None and vmax is None:
                return u'anything'
            elif vmin is None:
                text = u'Up to {}'.format(vmax)
            elif vmax is None:
                text = u'At least {}'.format(vmin)
            elif vmin == vmax:
                text = vmin
            else:
                text = u'%s–%s' % (vmin, vmax)

            if character.unit in (None, u'', u'NA'):
                return text
            else:
                return u'{} {}'.format(text, character.unit)

    else:
        return ''


@vary_on_headers('Host')
def species_view(request, genus_slug, epithet):

    COMPACT_MULTIVALUE_CHARACTERS = ['Habitat', 'New England state',
                                     'Specific Habitat']

    genus_name = genus_slug.capitalize()
    scientific_name = '%s %s' % (genus_name, epithet)
    taxon = get_object_or_404(Taxon, scientific_name=scientific_name)

    scientific_name_short = '%s. %s' % (scientific_name[0], epithet)

    pile_slug = request.GET.get('pile')
    if pile_slug:
        pile = get_object_or_404(Pile, slug=pile_slug)
    else:
        # Randomly grab the first pile from the species
        pile = taxon.piles.order_by('id')[0]
    pilegroup = pile.pilegroup

    partner = which_partner(request)
    partner_species = None
    if partner:
        rows = PartnerSpecies.objects.filter(
            species=taxon, partner=partner).all()
        if rows:
            partner_species = rows[0]

    dkey_pages = dkey_models.Page.objects.filter(title=scientific_name)
    dkey_page = dkey_pages[0] if dkey_pages else None

    dkey_hybrids = (dkey_models.Hybrid.objects
                    .filter(Q(scientific_name1=scientific_name) |
                            Q(scientific_name2=scientific_name))
                    .order_by('number1', 'number2'))

    species_in_simple_key = (partner_species and partner_species.simple_key)
    key = request.GET.get('key')
    if not key:
        if species_in_simple_key:
            key = 'simple'
        else:
            key = 'full'

    species_images = botany.species_images(taxon)
    images = _images_with_copyright_holders(species_images)

    # Get the set of preview characteristics.

    plant_preview_characters = {
        ppc.character_id: ppc.order for ppc in
        PlantPreviewCharacter.objects.filter(pile=pile, partner_site=partner)
        }
    # If no preview characteristics are defined for a partner, use the
    # ones defined for Go Botany.
    if len(plant_preview_characters) == 0:
        gobotany = PartnerSite.objects.get(short_name='gobotany')
        plant_preview_characters = {
            ppc.character_id: ppc.order for ppc in
            PlantPreviewCharacter.objects.filter(pile=pile,
                                                 partner_site=gobotany)
            }

    # Select ALL character values for this taxon.

    character_values = list(taxon.character_values.select_related(
            'character', 'character__character_group'))

    # Throw away values for characters that are not part of this pile.

    pile_ids = (None, pile.id)  # characters like 'habitat' have pile_id None

    # TODO: eventually remove this temporary code after the Remaining
    # Non-Monocots pile character value data is split and assigned.
    if pile.name.find('Remaining Non-Monocots') > -1:
        try:
            # Include the big pile which has the character value data.
            big_pile = Pile.objects.get(name='Remaining Non-Monocots')
            pile_ids = pile_ids + (big_pile.id,)
        except models.Pile.DoesNotExist:
            pass
    # (end of temporary code)

    character_values = [ v for v in character_values
                         if v.character.pile_id in pile_ids ]

    # Create a tree of character groups, characters, and values.

    get_group_name = lambda v: v.character.character_group.name
    get_character_name = lambda v: v.character.friendly_name

    character_values.sort(key=get_character_name)
    character_values.sort(key=get_group_name)

    all_characteristics = []
    for group_name, seq1 in groupby(character_values, get_group_name):
        characters = []

        for character_name, seq2 in groupby(seq1, get_character_name):
            seq2 = list(seq2)
            character = seq2[0].character  # arbitrary; all look the same
            characters.append({
                'group': character.character_group.name,
                'name': character.friendly_name,
                'values': sorted(_format_character_value(v) for v in seq2),
                'in_preview': character.id in plant_preview_characters,
                'preview_order': plant_preview_characters.get(character.id, -1),
                })

        all_characteristics.append({
            'name': group_name,
            'characters': characters
            })

    # Pick out the few preview characters for separate display.

    preview_characters = sorted((
        character
        for group in all_characteristics
        for character in group['characters']
        if character['in_preview']
        ), key=itemgetter('preview_order'))

    native_to_north_america = _native_to_north_america_status(taxon)

    return render_to_response_per_partner('species.html', {
           'pilegroup': pilegroup,
           'pile': pile,
           'scientific_name': scientific_name,
           'scientific_name_short': scientific_name_short,
           'taxon': taxon,
           'key': key,
           'species_in_simple_key': species_in_simple_key,
           'common_names': taxon.common_names.all(),  # view uses this 3 times
           'conservation_status_rows': (
                'endangered', 'threatened', 'special concern', 'historic',
                'rare', 'extirpated', 'invasive', 'prohibited',
                ),
           'dkey_hybrids': dkey_hybrids,
           'dkey_page': dkey_page,
           'images': images,
           'partner_heading': partner_species.species_page_heading
               if partner_species else None,
           'partner_blurb': partner_species.species_page_blurb
               if partner_species else None,
           'compact_multivalue_characters': COMPACT_MULTIVALUE_CHARACTERS,
           'brief_characteristics': preview_characters,
           'all_characteristics': all_characteristics,
           'epithet': epithet,
           'native_to_north_america': native_to_north_america
           }, request)
