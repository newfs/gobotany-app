from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from gobotany.plantshare.forms import NewSightingForm

def plantshare_view(request):
    return render_to_response('plantshare.html', {
           }, context_instance=RequestContext(request))

def sightings_view(request):
    return render_to_response('sightings.html', {
           }, context_instance=RequestContext(request))

@login_required
def new_sighting_view(request):
    if request.method == 'POST':
        form = NewSightingForm(request.POST)
        if form.is_valid():
            # TODO: process the data in form.cleaned_data
            return HttpResponseRedirect(reverse('ps-new-sighting-done'))
    else:
        form = NewSightingForm()
    return render(request, 'new_sighting.html', {
        'form': form,
    })

@login_required
def new_sighting_done_view(request):
    return render_to_response('new_sighting_done.html', {
           }, context_instance=RequestContext(request))

@login_required
def profile_view(request):
    return render_to_response('profile.html', {
           }, context_instance=RequestContext(request))
