from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

def plantshare_view(request):
    return render_to_response('plantshare.html', {
           }, context_instance=RequestContext(request))

@login_required
def new_sighting_view(request):
    return render_to_response('new_sighting.html', {
           }, context_instance=RequestContext(request))

def profile_view(request):
    return render_to_response('profile.html', {
           }, context_instance=RequestContext(request))
