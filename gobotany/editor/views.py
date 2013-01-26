import json
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from itertools import groupby
from operator import attrgetter as pluck

from gobotany.core import models
from gobotany.core.partner import which_partner


def e404(request):
    raise Http404()


@permission_required('botanist')
def piles_view(request):
    return render_to_response('gobotany/edit_piles.html', {
        'piles' : models.Pile.objects.all(),
        }, context_instance=RequestContext(request))


@permission_required('botanist')
def pile_characters(request, pile_slug):
    return render_to_response('gobotany/pile_characters.html', {
        'common_characters': models.Character.objects.filter(
            short_name__in=models.COMMON_CHARACTERS),
        'pile' : get_object_or_404(models.Pile, slug=pile_slug),
        }, context_instance=RequestContext(request))


@permission_required('botanist')
def edit_pile_character(request, pile_slug, character_slug):

    pile = get_object_or_404(models.Pile, slug=pile_slug)
    character = get_object_or_404(models.Character, short_name=character_slug)
    taxa = list(pile.species.all())

    if character.value_type == 'LENGTH':
        return _edit_pile_length_character(request, pile, character, taxa)
    else:
        return _edit_pile_string_character(request, pile, character, taxa)


def _edit_pile_length_character(request, pile, character, taxa):

    # There is little point in being heroic and trying to create exactly
    # one character value for a pair of

    taxon_ids = {taxon.id for taxon in taxa}
    taxon_values = {}
    minmaxes = {taxon.id: [None, None] for taxon in taxa}

    for tcv in models.TaxonCharacterValue.objects.filter(
            taxon__in=taxa, character_value__character=character
          ).select_related('character_value'):
        v = tcv.character_value
        taxon_values[tcv.taxon_id] = v
        minmaxes[tcv.taxon_id] = [v.value_min, v.value_max]

    # Process a POST.

    if 'value_settings' in request.POST:

        taxa_by_name = { taxon.scientific_name: taxon for taxon in taxa }
        value_settings = json.loads(request.POST['value_settings'])
        print value_settings

        for scientific_name, min_value, max_value in value_settings:
            scientific_name = scientific_name.replace(' (fk)', '')
            taxon = taxa_by_name[scientific_name]
            already_exists = taxon.id in taxon_values

            if already_exists:
                value = taxon_values[taxon.id]
            else:
                value = models.CharacterValue()
                value.character = character

            value.value_min = min_value
            value.value_max = max_value
            value.save()

            if not already_exists:
                tcv = models.TaxonCharacterValue()
                tcv.character_value = value
                tcv.taxon = taxon
                tcv.save()

        return redirect(request.path)

    # Grabbing one copy of each family once is noticeably faster than
    # using select_related('family') up in the taxon fetch:

    family_ids = set(t.family_id for t in taxa)
    families = models.Family.objects.filter(id__in=family_ids)

    taxa.sort(key=pluck('family_id'))  # always sort() before groupby()!
    taxa_by_family_id = { family_id: list(group) for family_id, group
                          in groupby(taxa, key=pluck('family_id')) }

    def grid():
        """Iterator across families and their taxa."""
        for family in families:
            yield 'family', family, None
            for taxon in taxa_by_family_id.get(family.id, ()):
                name = taxon.scientific_name
                if taxon.id not in simple_ids:
                    name += ' (fk)'
                yield 'taxon', name, minmaxes[taxon.id]

    partner = which_partner(request)
    simple_ids = set(ps.species_id for ps in models.PartnerSpecies.objects
                     .filter(partner_id=partner.id, simple_key=True))

    valued_ids = {id for id, value in minmaxes.items() if value != ['', ''] }
    coverage_percent_full = len(valued_ids) * 100.0 / len(taxa)
    coverage_percent_simple = (len(simple_ids.intersection(valued_ids))
                     * 100.0 / len(simple_ids.intersection(taxon_ids)))

    return render_to_response('gobotany/edit_pile_length.html', {
        'character': character,
        'coverage_percent_full': coverage_percent_full,
        'coverage_percent_simple': coverage_percent_simple,
        'grid': grid(),
        'pile': pile,
        }, context_instance=RequestContext(request))


def _edit_pile_string_character(request, pile, character, taxa):

    values = list(character.character_values.all())
    values.sort(key=character_value_key)

    tcvlist = list(models.TaxonCharacterValue.objects
                   .filter(taxon__in=taxa, character_value__in=values))
    value_map = {(tcv.taxon_id, tcv.character_value_id): tcv
                 for tcv in tcvlist}

    # We now have enough information, and can either handle a POST
    # update of specific data or a GET that displays the whole pile.

    if 'new_values' in request.POST:
        new_values = request.POST['new_values']
        _save(new_values, character=character)
        return redirect(request.path)

    # Grabbing one copy of each family once is noticeably faster than
    # using select_related('family') up in the taxon fetch:

    family_ids = set(t.family_id for t in taxa)
    families = models.Family.objects.filter(id__in=family_ids)

    taxa.sort(key=pluck('family_id'))  # always sort() before groupby()!
    taxa_by_family_id = { family_id: list(group) for family_id, group
                          in groupby(taxa, key=pluck('family_id')) }

    partner = which_partner(request)
    simple_ids = set(ps.species_id for ps in models.PartnerSpecies.objects
                     .filter(partner_id=partner.id, simple_key=True))

    # This view takes far too long to render with slow Django templates,
    # so we simply deliver JSON data for the front-end to render there.

    def grid():
        for family in sorted(families, key=pluck('name')):
            yield [family.name]
            family_taxa = taxa_by_family_id[family.id]
            for taxon in family_taxa:
                vector = ''.join(
                    '1' if (taxon.id, value.id) in value_map else '0'
                    for value in values
                    )
                name = taxon.scientific_name
                if taxon.id not in simple_ids:
                    name += ' (fk)'
                yield [name, vector]

    taxa_with_values = set(tcv.taxon_id for tcv in tcvlist)
    taxa_ids = set(taxon.id for taxon in taxa)

    coverage_percent_full = len(taxa_with_values) * 100.0 / len(taxa)
    coverage_percent_simple = (len(simple_ids.intersection(taxa_with_values))
                     * 100.0 / len(simple_ids.intersection(taxa_ids)))

    return render_to_response('gobotany/edit_pile_character.html', {
        'there_are_any_friendly_texts': any(v.friendly_text for v in values),
        'character': character,
        'coverage_percent_full': coverage_percent_full,
        'coverage_percent_simple': coverage_percent_simple,
        'grid': json.dumps(list(grid())),
        'pile': pile,
        'values': values,
        'values_json': json.dumps([value.value_str for value in values]),
        }, context_instance=RequestContext(request))


@permission_required('botanist')
def pile_taxa(request, pile_slug):
    return render_to_response('gobotany/pile_taxa.html', {
        'pile' : get_object_or_404(models.Pile, slug=pile_slug),
        }, context_instance=RequestContext(request))


@permission_required('botanist')
def edit_pile_taxon(request, pile_slug, taxon_slug):

    name = taxon_slug.capitalize().replace('-', ' ')

    pile = get_object_or_404(models.Pile, slug=pile_slug)
    taxon = get_object_or_404(models.Taxon, scientific_name=name)

    common_characters = list(models.Character.objects.filter(
            short_name__in=models.COMMON_CHARACTERS, value_type=u'TEXT'))
    pile_characters = list(pile.characters.filter(value_type=u'TEXT'))

    tcvlist = list(models.TaxonCharacterValue.objects.filter(taxon=taxon))

    # A POST updates the taxon and redirects, instead of rendering.

    if 'new_values' in request.POST:
        new_values = request.POST['new_values']
        _save(new_values, taxon=taxon)
        return redirect(request.path)

    # Yield a sequence of characters.
    # Each character has .values, a sorted list of character values
    # Each value has .checked, indicating that the species has it.

    value_map = {(tcv.taxon_id, tcv.character_value_id): tcv
                 for tcv in tcvlist}

    def annotated_characters(characters):
        def generator():
            for character in characters:
                character.values = list(character.character_values.all())
                character.values.sort(key=character_value_key)
                for value in character.values:
                    value.checked = (taxon.id, value.id) in value_map
                    if value.checked:
                        character.is_any_value_checked = True
                yield character
        return generator

    return render_to_response('gobotany/edit_pile_taxon.html', {
        'common_characters': annotated_characters(common_characters),
        'pile': pile,
        'pile_characters': annotated_characters(pile_characters),
        'taxon': taxon,
        }, context_instance=RequestContext(request))


def _save(new_values, character=None, taxon=None):
    new_values = json.loads(new_values)

    if character is None:
        get_character = models.Character.objects.get
        character_taxon_value_tuples = [
            (get_character(short_name=name), taxon, v)
            for (name, v) in new_values
            ]
    elif taxon is None:
        get_taxon = models.Taxon.objects.get
        character_taxon_value_tuples = [
            (character, get_taxon(scientific_name=name), v)
            for (name, v) in new_values
            ]

    for character, taxon, value in character_taxon_value_tuples:
        if character.value_type == 'LENGTH':
            _save_length(character, taxon, value)
        else:
            _save_textual(character, taxon, value)


def _save_length(character, taxon, minmax):
    raise NotImplementedError()


def _save_textual(character, taxon, vector):
    values = list(character.character_values.all())
    values.sort(key=character_value_key)

    tcvs = list(models.TaxonCharacterValue.objects.filter(
        character_value__in=values, taxon=taxon))
    tcvmap = {tcv.character_value_id: tcv for tcv in tcvs}

    for value, digit in zip(values, vector):
        bit = (digit == '1')
        if bit and (value.id not in tcvmap):
            models.TaxonCharacterValue(
                taxon=taxon, character_value=value).save()
        elif (not bit) and (value.id in tcvmap):
            tcvmap[value.id].delete()


def character_value_key(cv):
    """Return a sort key that puts 'NA' last."""

    v = cv.value_str.lower()
    if v == 'na':
        return 'zzzz'
    return v
