# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext

def about_view(request):
    return render_to_response('gobotany/about.html', {
           }, context_instance=RequestContext(request))
