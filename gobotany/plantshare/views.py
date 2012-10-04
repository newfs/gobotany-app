from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from gobotany.plantshare.forms import NewSightingForm

def _new_sighting_form_page(request, form):
    """Give a new-sighting form, either blank or with as-yet-invalid data."""
    return render(request, 'new_sighting.html', {
               'form': form,
           }, context_instance=RequestContext(request))

# Views

def plantshare_view(request):
    """View for the main PlantShare page."""
    return render_to_response('plantshare.html', {
           }, context_instance=RequestContext(request))

def sightings_view(request):
    """View for the sightings collection, and handling new sightings."""
    if request.method == 'POST':
        # Handle posting a new sighting to the sightings collection.
        # TODO: require login for just this HTTP verb.
        form = NewSightingForm(request.POST)
        if form.is_valid():
            # TODO: process the data in form.cleaned_data
            #print 'form.cleaned_data:', form.cleaned_data
            return HttpResponseRedirect(reverse('ps-new-sighting-done')) # ?
        else:
            # Present the new-sighting form again for input correction.
            return _new_sighting_form_page(request, form)
    elif request.method == 'GET':
        # Return a representation of the collection of sightings.
        return render_to_response('sightings.html', {
               }, context_instance=RequestContext(request))
    else:
        # For an unsupported HTTP method, return a Bad Request response.
        return HttpResponse(status=400)

@login_required
def new_sighting_view(request):
    """View for a blank form for posting a new sighting."""
    form = NewSightingForm()
    return _new_sighting_form_page(request, form)

@login_required
def new_sighting_done_view(request):
    """View for a confirmation page upon posting a new sighting."""
    return render_to_response('new_sighting_done.html', {
           }, context_instance=RequestContext(request))

@login_required
def profile_view(request):
    """View for the logged-in user's profile."""
    return render_to_response('profile.html', {
           }, context_instance=RequestContext(request))
