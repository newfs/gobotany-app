import os
from collections import defaultdict
from operator import attrgetter
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
    possible values"""

    def __init__(self, pile_name, *args, **kwargs):
        """Iterate over pile characters and create widgets with the values"""
        super(PileSearchForm, self).__init__(*args, **kwargs)
        characters = models.Character.objects.filter(
                    character_values__pile__name__iexact=pile_name).order_by(
                                                            'character_group',
                                                            'short_name')
        character_values = models.CharacterValue.objects
        for character in characters:
            try:
                term = character.glossary_terms.get(
                    glossarytermforpilecharacter__pile__name__iexact=pile_name)
                label = '%s: %s'%(term.term, term.question_text)
            except models.GlossaryTerm.DoesNotExist:
                label=character.short_name
            self.fields[character.short_name] = forms.ChoiceField(
                label=label,
                required=False,
                choices=[('', '----------')]+[(c.value_str, (c.glossary_term and c.glossary_term.lay_definition) and "%s - %s"%(c.glossary_term.term, c.glossary_term.lay_definition) or c.value_str) for c in
                         character_values.filter(character=character)])


def piles_pile_groups(request):
    return render_to_response('piles_pile_groups.html',
                              context_instance=RequestContext(request))


def pile_search(request, pile_name):
    data = []
    if request.method == 'POST':
        form = PileSearchForm(pile_name, request.POST)
        if form.is_valid():
            params = dict((str(k),v) for k,v in form.cleaned_data.iteritems() if v)
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

def glossary_index(request):
    # Case-insensitive sort
    glossary = models.GlossaryTerm.objects.filter(visible=True).extra(
        select={'lower_term': 'lower(term)'}).order_by('lower_term')
    return render_to_response('glossary.html', {'glossary': glossary},
                              context_instance=RequestContext(request))

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
                'url': '/taxon/?' + urlencode({'pilegroup': pilegroup.name}),
                })

    for pile in models.Pile.objects.all():
        biglist.append({
                'name': 'Pile ' + pile.name,
                'url': '/taxon/?' + urlencode({'pile': pile.name}),
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

    pile = models.Pile.objects.get(slug=pile_slug)
    species_list = pile.species.all()
    species_ids = sorted( s.id for s in species_list )
    entropy_character_id_list = igdt.get_best_characters(pile, species_ids)

    cvs = pile.character_values.all()
    cvs_by_cid = defaultdict(list)
    for cv in cvs:
        cvs_by_cid[cv.character_id].append(cv)

    clist = []

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

        character_values = list(cvs_by_cid[character.id]) # 'cause we mutate it
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

        relevant_tcvs = models.TaxonCharacterValue.objects.filter(
            taxon__in=species_list,
            character_value__in=character_values,
            )
        for tcv in relevant_tcvs:
            yn_sequence = species_grid_dict[tcv.taxon_id]
            index = character_values.index(tcv.character_value)
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
            metarows.append((
                character_value.value_str, row.count('Y'), row
                ))

        return metarows, species_row

    for entropy, character_id in entropy_character_id_list:
        character = models.Character.objects.get(id=character_id)
        if character.value_type != 'TEXT':
            continue  # do not even bother with lengths yet!
        metarows, species_row = _tablefy_data(character)
        clist.append({
                'entropy': entropy,
                'ease_of_observability': character.ease_of_observability,
                'name': character.name,
                'type': character.value_type,
                'num_values': len(cvs_by_cid[character.id]),
                'metarows': metarows,
                'species_row': species_row,
                })

    return render_to_response('pile_characters.html', {
            'pile': pile,
            'width': WIDTH,
            'characters': clist,
            })
