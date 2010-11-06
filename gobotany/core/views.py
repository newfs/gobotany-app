import os
import time
from collections import defaultdict
from operator import attrgetter, itemgetter
from urllib import urlencode

from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms
from django.views import static 

from gobotany.core import botany, igdt, models


def default_view(request):
    return render_to_response('index.html', {},
                              context_instance=RequestContext(request))


class PileSearchForm(forms.Form):
    """A form listing all botanic characters for a pile along with
    possible values. For now only characters with text values are shown.
    """

    def __init__(self, pile_name, *args, **kwargs):
        """Iterate over pile characters and create widgets with the values"""
        super(PileSearchForm, self).__init__(*args, **kwargs)
        characters = models.Character.objects.filter(
                    character_values__pile__name__iexact=pile_name,
                    value_type='TEXT').order_by('character_group',
                                                'short_name')
        character_values = models.CharacterValue.objects
        for character in characters:
            try:
                term = character.glossary_terms.get(
                    glossarytermforpilecharacter__pile__name__iexact=pile_name)
                label = '%s: %s'%(term.term, term.question_text)
            except models.GlossaryTerm.DoesNotExist:
                label=character.short_name
            choices = [('', '----------')] + [(c.value_str, \
                (c.glossary_term and c.glossary_term.lay_definition) and \
                "%s - %s" % (c.glossary_term.term, \
                c.glossary_term.lay_definition) or c.value_str) for c in \
                character_values.filter(character=character)]
            self.fields[character.short_name] = forms.ChoiceField(label=label,
                required=False, choices=choices)


def piles_pile_groups(request):
    return render_to_response('piles_pile_groups.html',
                              context_instance=RequestContext(request))


def pile_search(request, pile_name):
    data = []
    if request.method == 'POST':
        form = PileSearchForm(pile_name, request.POST)
        if form.is_valid():
            params = dict((str(k), v) for k, v in \
                     form.cleaned_data.iteritems() if v)
            data = botany.query_species(**params)
    else:
        form = PileSearchForm(pile_name)
    return render_to_response('pile_search.html',
                              {'pile': pile_name,
                               'form': form,
                               'data': data,
                               'submitted': request.method == 'POST'},
                              context_instance=RequestContext(request))


def taxon_search(request):
    kwargs = {}
    if request.method == 'POST':
        kwargs['queried'] = True
        s = kwargs['s'] = request.POST['s'].strip()
        kwargs['query_results'] = botany.query_species(
            scientific_name=s)

    return render_to_response('taxon_search.html', kwargs,
                               context_instance=RequestContext(request))


def static_serve(request, path, package=None,
                 relative_path='', show_indexes=False):
    document_root = package.__path__[0]
    if relative_path:
        document_root = os.path.join(document_root, relative_path)

    return static.serve(request, path, document_root=document_root,
                        show_indexes=show_indexes)

def canonical_images(request):
    results = []
    if request.method == 'POST':
        s = request.POST['s'].strip()
        results = botany.species_images(s, max_rank=1)
    return render_to_response('canonical_images.html', 
                                {'results': results},
                                context_instance=RequestContext(request))

def species_lists(request):
    biglist = []

    for pilegroup in models.PileGroup.objects.all():
        biglist.append({
                'name': 'Pile-Group ' + pilegroup.name,
                'url': '/taxon/?' + urlencode({'pilegroup': pilegroup.slug}),
                })

    for pile in models.Pile.objects.all():
        biglist.append({
                'name': 'Pile ' + pile.name,
                'url': '/taxon/?' + urlencode({'pile': pile.slug}),
                })

    species_names = [ t.scientific_name for t in models.Taxon.objects.all() ]
    genus_names = sorted(set( name.split()[0] for name in species_names ))
    for genus_name in genus_names:
        biglist.append({
                'name': 'Genus ' + genus_name,
                'url': '/taxon/?' + urlencode({'genus': genus_name}),
                })

    return render_to_response('species_lists.html', {
            'biglist': biglist,
            })


def pile_characters_select(request):
    return render_to_response('pile_characters_select.html', {
            'piles': [ (pile.slug, pile.name) for pile
                       in models.Pile.objects.order_by('name') ],
            })


def pile_characters(request, pile_slug):
    WIDTH = 500

    coverage_weight, ease_weight, length_weight = igdt.get_weights()

    coverage_parameter, created = models.Parameter.objects.get_or_create(
        name='coverage_weight', defaults={'value': coverage_weight})
    ease_parameter, created = models.Parameter.objects.get_or_create(
        name='ease_of_observability_weight', defaults={'value': ease_weight})
    length_parameter, created = models.Parameter.objects.get_or_create(
        name='length_weight', defaults={'value': length_weight})

    try:
        coverage_weight = float(request.GET['coverage_weight'])
    except (KeyError, ValueError):
        pass

    try:
        ease_weight = float(request.GET['ease_weight'])
    except (KeyError, ValueError):
        pass

    try:
        length_weight = float(request.GET['length_weight'])
    except (KeyError, ValueError):
        pass

    pile = models.Pile.objects.get(slug=pile_slug)
    species_list = pile.species.all()
    species_ids = sorted( s.id for s in species_list )
    species_by_id = dict( (s.id, s) for s in species_list )
    t0 = time.time()
    character_entropy_list = igdt.compute_character_entropies(pile,
                                                              species_ids)
    elapsed_time = time.time() - t0

    cvs = pile.character_values.all()
    cvs_by_cid = defaultdict(list)
    for cv in cvs:
        cvs_by_cid[cv.character_id].append(cv)

    clist = []

    # Pre-fetch character and taxon objets, since doing so - even though
    # we are grabbing everything in the database when we are just
    # interested in one pile! - is much faster than having the Django
    # ORM go fetch them over and over hundreds of times.

    character_values_by_id = dict(
        (cv.id, cv) for cv in models.CharacterValue.objects.all()
        )

    tcvs_by_cv_id = defaultdict(list)
    for tcv in models.TaxonCharacterValue.objects.all():
        tcvs_by_cv_id[tcv.character_value_id].append(tcv)

    #

    def _tablefy_data(character):
        """Create a matrix showing which species have which char values."""

        # At this point we already have species IDs for this pile, and
        # character value IDs for this character; so without having to
        # do an expensive join, we can directly query the table
        # TaxonCharacterValue to see which species have which character
        # values.  For each species we create a list ['Y','n','Y',...]
        # where each 'Y' or 'n' corresponds to the nth value in our
        # `values` list.  (The Y is capitalized so that it sorts first.)

        # Sort character values by value_str, lexicographically.

        character_values = list(cvs_by_cid[character.id]) # cause we mutate it
        character_values.sort(key=attrgetter('value_str'))

        for i, cv in enumerate(character_values):
            if cv.value_str == 'NA':
                character_values.append(character_values[i])
                del character_values[i]  # move NA to the end
                break

        # Create a "blank" grid of 'n' strings.

        species_grid_dict = {}
        for species_id in species_ids:
            species_grid_dict[species_id] = ['n'] * len(character_values)

        # Fill in a 'Y' for each species/character-value pair.

        for cv in character_values:
            for tcv in tcvs_by_cv_id[cv.id]:
                if tcv.taxon_id in species_by_id:
                    yn_sequence = species_grid_dict[tcv.taxon_id]
                    cv = character_values_by_id[tcv.character_value_id]
                    index = character_values.index(cv)
                    yn_sequence[index] = 'Y'

        # Add a last value for each species, that is checked if a
        # species had no values at all for this character.

        for yn_sequence in species_grid_dict.values():
            yn_sequence.append( 'n' if 'Y' in yn_sequence else 'Y' )

        warning_value = models.CharacterValue()
        warning_value.value_str = None
        character_values.append(warning_value)

        # Sort and re-orient the table for display.  We temporarily
        # throw the species on to the end of each row, so that during
        # the re-order we can keep up with which row went with which
        # species.

        columns = species_grid_dict.values()
        for column, species in zip(columns, species_list):
            column.append(species)
        columns.sort()
        rows = [ list(row) for row in zip(*columns) ]

        # Pop off the bottom row of species, which we will pass as a
        # separate variable to the template.

        species_row = rows.pop()

        # Make a list of meta-information about each row that includes
        # the row itself.

        metarows = []
        for row, character_value in zip(rows, character_values):
            if character.value_type == u'TEXT':
                name = character_value.value_str
            elif character.value_type == u'LENGTH':
                if (character_value.value_min == 0.0 and
                    character_value.value_max == 0.0):
                    name = 'NA'
                elif (character_value.value_min is None or
                      character_value.value_max is None):
                    name = 'NULL'
                else:
                    name = '%s - %s' % (character_value.value_min,
                                        character_value.value_max)
            elif character_value.value_type == u'RATIO':
                name = 'float %s' % (character_value.value_flt,)
            else:
                name = 'UNKNOWN VALUE TYPE'
            metarows.append((
                name, row.count('Y'), row
                ))

        return metarows, species_row

    #

    def _graphify_data(character):
        """Compile data for a bar graph of min-max character values."""
        character_values = list(cvs_by_cid[character.id])

        vmin = min( cv.value_min for cv in character_values
                    if cv.value_min is not None )
        vmax = max( cv.value_max for cv in character_values
                    if cv.value_max is not None )

        scale = WIDTH / (vmax - vmin)
        metarows = []
        for cv in character_values:
            if cv.value_min is None or cv.value_max is None:
                continue
            x0 = int(scale * (cv.value_min - vmin))
            x1 = int(scale * (cv.value_max - vmin))
            width = x1 - x0
            species = [ species_by_id[tcv.taxon_id]
                        for tcv in tcvs_by_cv_id[cv.id]
                        if tcv.taxon_id in species_by_id ]
            metarows.append([ x0, width, cv.value_min, cv.value_max, species ])

        return metarows, None

    #

    character_ids = [ item[0] for item in character_entropy_list ]
    characters_by_id = dict(
        (character.id, character) for character
        in models.Character.objects.filter(id__in=character_ids)
        )

    for character_id, entropy, coverage in character_entropy_list:
        character = characters_by_id[character_id]
        if character.value_type == u'TEXT':
            metarows, species_row = _tablefy_data(character)
        elif character.value_type == u'LENGTH':
            metarows, species_row = _graphify_data(character)
        else:
            continue  # do not bother with ratio values yet
        ease = character.ease_of_observability
        score = igdt.compute_score(
            entropy, coverage, ease, character.value_type,
            coverage_weight, ease_weight, length_weight)
        clist.append({
                'entropy': entropy,
                'coverage': coverage,
                'ease_of_observability': ease,
                'score': score,
                'name': character.name,
                'type': character.value_type,
                'num_values': len(cvs_by_cid[character.id]),
                'metarows': metarows,
                'species_row': species_row,
                })

    clist.sort(key=itemgetter('score'))

    return render_to_response('pile_characters.html', {
            'pile': pile,
            'elapsed_time': elapsed_time,
            'width': WIDTH,
            'characters': clist,
            'coverage_parameter': coverage_parameter,
            'ease_parameter': ease_parameter,
            'length_parameter': length_parameter,
            'coverage_weight': coverage_weight,
            'ease_weight': ease_weight,
            'length_weight': length_weight,
            })


#
# Since the pile_characters function above refuses to return an
# exception message in less than ten minutes (Django's exception page
# simply refuses to render in a reasonable amount of time,) here is a
# wrapper that prints a normal traceback:
#

_func = pile_characters
def pile_characters(*args, **kw):
    try:
        return _func(*args, **kw)
    except Exception:
        from django.http import HttpResponse
        import traceback
        return HttpResponse(traceback.format_exc(), mimetype='text/plain')
