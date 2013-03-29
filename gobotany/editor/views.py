import json
import re
import urllib
from itertools import groupby
from operator import attrgetter as pluck

import tablib
from datetime import datetime
from django.contrib.auth.decorators import permission_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.utils import timezone
from shoehorn.engine import DifferenceEngine

from gobotany.core import models
from gobotany.core.partner import which_partner
from . import wranglers


def e404(request):
    raise Http404()


@permission_required('core.botanist')
def piles_view(request):
    return render_to_response('gobotany/edit_piles.html', {
        'piles' : models.Pile.objects.all(),
        }, context_instance=RequestContext(request))


@permission_required('core.botanist')
def pile_characters(request, pile_slug):
    return render_to_response('gobotany/pile_characters.html', {
        'common_characters': models.Character.objects.filter(
            short_name__in=models.COMMON_CHARACTERS),
        'pile' : get_object_or_404(models.Pile, slug=pile_slug),
        }, context_instance=RequestContext(request))


@permission_required('core.botanist')
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

    if 'new_values' in request.POST:
        new_values = request.POST['new_values']
        return _save(request, new_values, character=character)

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
        return _save(request, new_values, character=character)

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


@permission_required('core.botanist')
def pile_taxa(request, pile_slug):
    return render_to_response('gobotany/pile_taxa.html', {
        'pile' : get_object_or_404(models.Pile, slug=pile_slug),
        }, context_instance=RequestContext(request))


@permission_required('core.botanist')
def edit_pile_taxon(request, pile_slug, taxon_slug):

    name = taxon_slug.capitalize().replace('-', ' ')

    pile = get_object_or_404(models.Pile, slug=pile_slug)
    taxon = get_object_or_404(models.Taxon, scientific_name=name)

    # A POST updates the taxon and redirects, instead of rendering.

    if 'new_values' in request.POST:
        new_values = request.POST['new_values']
        return _save(request, new_values, taxon=taxon)

    # Yield a sequence of characters.
    # Each character has .values, a sorted list of character values
    # Each value has .checked, indicating that the species has it.

    common_characters = list(models.Character.objects.filter(
            short_name__in=models.COMMON_CHARACTERS, value_type=u'TEXT'))
    pile_characters = list(pile.characters.all())

    tcvlist = list(models.TaxonCharacterValue.objects.filter(taxon=taxon)
                   .select_related('character_value'))
    value_map1 = {tcv.character_value_id: tcv for tcv in tcvlist}
    value_map2 = {tcv.character_value.character_id: tcv.character_value
                  for tcv in tcvlist}

    def annotated_characters(characters):
        def generator():
            for character in characters:

                if character.value_type == 'LENGTH':
                    value = value_map2.get(character.id)
                    if value is None:
                        character.min = None
                        character.max = None
                    else:
                        character.min = value.value_min
                        character.max = value.value_max

                else:
                    character.values = list(character.character_values.all())
                    character.values.sort(key=character_value_key)
                    for value in character.values:
                        value.checked = (value.id in value_map1)
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


def _save(request, new_values, character=None, taxon=None):
    dt = timezone.now()
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
            old_value = _save_length(request, character, taxon, value)
        else:
            old_value = _save_textual(request, character, taxon, value)

        models.Edit(
            author=request.user.username,
            datetime=dt,
            itemtype='character-value',
            coordinate1=taxon.scientific_name,
            coordinate2=character.short_name,
            old_value=json.dumps(old_value),
            ).save()

    return redirect(dt.strftime(
        '/edit/cv/lit-sources/%Y.%m.%d.%H.%M.%S.%f/?return_to='
        + urllib.quote(request.path)))

def _save_length(request, character, taxon, minmax):

    tcvs = list(models.TaxonCharacterValue.objects
                .filter(character_value__character=character, taxon=taxon)
                .select_related('character_value'))

    if tcvs:
        tcv = tcvs[0]
        value = tcv.character_value
        old_values = [value.value_min, value.value_max]
        is_value_shared = len(value.taxon_character_values.all())

        if is_value_shared:
            tcv.delete()
        else:
            value.value_min = minmax[0]
            value.value_max = minmax[1]
            value.save()
            return
    else:
        old_values = [None, None]

    value = models.CharacterValue(
        character=character,
        value_min=minmax[0],
        value_max=minmax[1],
        )
    value.save()

    models.TaxonCharacterValue(character_value=value, taxon=taxon).save()
    return old_values


def _save_textual(request, character, taxon, vector):
    values = list(character.character_values.all())
    values.sort(key=character_value_key)

    tcvs = list(models.TaxonCharacterValue.objects.filter(
        character_value__in=values, taxon=taxon))
    tcvmap = {tcv.character_value_id: tcv for tcv in tcvs}

    old_values = []

    for value, digit in zip(values, vector):
        has_it = value.id in tcvmap
        needs_it = digit == '1'

        if has_it:
            old_values.append(value.value_str)

        if needs_it and not has_it:
            models.TaxonCharacterValue(
                taxon=taxon, character_value=value).save()
        elif not needs_it and has_it:
            tcvmap[value.id].delete()

    return old_values


def character_value_key(cv):
    """Return a sort key that puts 'NA' last."""

    v = cv.value_str.lower()
    if v == 'na':
        return 'zzzz'
    return v


tcvfieldname_re = re.compile('tcv([0-9]+)$')

@permission_required('core.botanist')
def edit_lit_sources(request, dotted_datetime):

    return_to = request.REQUEST.get('return_to', '.')

    if request.method == 'POST':
        for key in request.POST:
            match = tcvfieldname_re.match(key)
            if not match:
                continue
            number = int(match.group(1))
            tcvs = models.TaxonCharacterValue.objects.filter(id=number)
            if not tcvs:
                # Ignore a tcv that has disappeared in the meantime.
                continue
            tcv = tcvs[0]
            tcv.lit_source = request.POST[key]
            tcv.save()
        return redirect(return_to)

    if dotted_datetime.count('.') != 6:
        raise Http404()

    integers = [int(field) for field in dotted_datetime.split('.')]
    year, month, day, hour, minute, second, us = integers
    d = datetime(year, month, day, hour, minute, second, us)
    d = timezone.make_aware(d, timezone.utc)
    edits = models.Edit.objects.filter(datetime=d, itemtype='character-value')

    # TODO: if no edits, jump away?

    tcvlist = []

    for edit in edits:
        taxon_name = edit.coordinate1
        short_name = edit.coordinate2
        taxon = models.Taxon.objects.get(scientific_name=taxon_name)
        character = models.Character.objects.get(short_name=short_name)
        tcvs = models.TaxonCharacterValue.objects.filter(
            taxon=taxon, character_value__character=character,
            ).select_related(
            'taxon character_value character_value__character'
            )
        tcvlist.extend(tcvs)

    return render_to_response('gobotany/edit_lit_sources.html', {
        'return_to': return_to,
        'tcvlist': tcvlist,
        }, context_instance=RequestContext(request))


@permission_required('core.botanist')
def partner_plants(request, idnum):
    partner = get_object_or_404(models.PartnerSite, id=idnum)
    plants = list(models.PartnerSpecies.objects
                  .filter(partner=partner)
                  .select_related('species')
                  .order_by('species__scientific_name'))
    return render_to_response('gobotany/view_partner_plants.html', {
        'download_url': '/edit/partner{}-plants.csv'.format(partner.id),
        'upload_url': 'upload/',
        'partner': partner,
        'plants': plants,
        }, context_instance=RequestContext(request))



@permission_required('core.botanist')
def partner_plants_upload(request, idnum):
    partner = get_object_or_404(models.PartnerSite, id=idnum)
    return_url = '..'
    printout = []
    changes = None

    if request.method == 'POST':

        # Step 3: they pressed "Confirm" so we make the changes.
        if 'changes' in request.POST:

            inserts, updates, deletes = json.loads(request.POST['changes'])

            for name, simple in inserts:
                taxon = models.Taxon.objects.filter(scientific_name=name)[0]
                ps = models.PartnerSpecies()
                ps.species = taxon
                ps.partner = partner
                ps.simple_key = (simple == 'yes')
                ps.save()

            for ((old_name, old_simple), (name, simple)) in updates:
                taxon = models.Taxon.objects.filter(scientific_name=name)[0]
                ps = (models.PartnerSpecies.objects
                      .filter(species=taxon, partner=partner)
                      )[0]
                ps.simple_key = (simple == 'yes')
                ps.save()

            for name, simple in deletes:
                taxon = models.Taxon.objects.filter(scientific_name=name)[0]
                ps = models.PartnerSpecies()
                ps = (models.PartnerSpecies.objects
                      .filter(species=taxon, partner=partner)
                      )[0]
                ps.delete()

            return redirect(return_url)

        # Step 2: they have selected a file and pressed "Upload".
        if 'csvfile' in request.FILES:
            upload_records = tablib.Dataset()
            upload_records.csv = request.FILES['csvfile'].read()
            wrangler = wranglers.PartnerPlants(partner)
            database_records = wrangler.generate_records()
            de = DifferenceEngine()
            de.differentiate(database_records, upload_records, [0])

            bad_inserts = [ record for record in de.inserts if not len(
                    models.Taxon.objects.filter(scientific_name=record[0])) ]
            if bad_inserts:
                printout.append(u'Unrecognized plants that will NOT be '
                                u'imported but ignored for now:')
                printout.append(u'')
                for bad in bad_inserts:
                    printout.append(u'- {}'.format(bad[0]))
                printout.append(u'')

            de.inserts = [ record for record in de.inserts
                           if record[0].lower() != 'scientific_name'
                              and record not in bad_inserts ]

            if de.inserts:
                printout.append(u'Plants to insert:')
                printout.append('')
                for record in de.inserts:
                    printout.append(u'- {}'.format(record[0]))
            else:
                printout.append(u'No plants to insert.')
            printout.append('')
            if de.updates:
                printout.append(u'Plants changing simple-key membership:')
                printout.append('')
                for record in de.updates:
                    printout.append(u'- {} changing to: {}'.format(*record[1]))
            else:
                printout.append(u'No plants to update.')
            printout.append('')
            if de.deletes:
                printout.append(u'Plants to remove from this partner:')
                printout.append('')
                for record in de.deletes:
                    printout.append(u'- {}'.format(record[0]))
            else:
                printout.append(u'No plants to delete.')
            printout.append('')

            changes = json.dumps([de.inserts, de.updates, de.deletes])
        else:
            printout.append(u'Please select a file for upload and try again.')

    # Step 1: an admin visits the page.
    return render_to_response('gobotany/upload_partner_plants.html', {
        'changes': changes,
        'partner': partner,
        'printout': '\n'.join(printout),
        'return_url': return_url,
        }, context_instance=RequestContext(request))


@permission_required('core.botanist')
def partner_plants_csv(request, idnum):
    partner = get_object_or_404(models.PartnerSite, id=idnum)
    wrangler = wranglers.PartnerPlants(partner)

    headers = ['scientific_name', 'belongs_in_simple_key']
    dataset = tablib.Dataset(headers=headers)
    for record in wrangler.generate_records():
        dataset.append(record)

    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="partner{}-plants.csv"'.format(partner.id)
        )
    return response
