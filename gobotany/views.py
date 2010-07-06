import os

from django.template import RequestContext
from django.shortcuts import render_to_response
from django import forms
from django.views import static 

from gobotany import botany, models


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
                    charactervalue__pile__name__iexact=pile_name).order_by(
                                                            'character_group',
                                                            'short_name')
        character_values = models.CharacterValue.objects
        for character in characters:
            try:
                label= character.short_name + ': ' + character.glossary_terms.get(glossarytermforpilecharacter__pile__name__iexact=pile_name).question_text
            except models.GlossaryTerm.DoesNotExist:
                label=character.short_name
            self.fields[character.short_name] = forms.ChoiceField(
                label=label,
                required=False,
                choices=[('', '----------')]+[(c.value_str, c.glossary_term and "%s: %s"%(c.glossary_term.term, c.glossary_term.lay_definition) or c.value_str) for c in
                         character_values.filter(character=character)]) 
                         

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
