"""Routines that help adapt Go Botany sites for different partners."""

import sys

from django.conf import settings
from django.http import Http404
from django.shortcuts import render_to_response
from django.template import Context, RequestContext, TemplateDoesNotExist

from gobotany.core.models import PartnerSite

def which_partner(request):
    """Determine which partner site is being viewed."""
    short_name = request.get_host().split('.', 1)[0]  # the 'foo' of 'foo.com'
    short_name = short_name.split('-', 1)[0]  # 'foo' if 'foo-dev.com'
    possibilities = (short_name, 'gobotany')
    matches = list(PartnerSite.objects.filter(short_name__in=(possibilities)))

    message = ('which_partner: request.get_host()=%s short_name=%s '
               'len(possibilities)=%d len(matches)=%d') % (
                request.get_host(), short_name, len(possibilities),
                len(matches))
    print >> sys.stderr, message

    matches_short_names = [match.short_name for match in matches]
    print >> sys.stderr, 'matches_short_names:', ' '.join(matches_short_names)

    match = None
    if len(matches) > 1 and matches[1].short_name == short_name:
        match = matches[1]
    elif len(matches):
        match = matches[0]

    print >> sys.stderr, 'about to return match:', match

    return match

def partner_short_name(request):
    partner = which_partner(request)
    if partner is None:
        return None
    return partner.short_name

def per_partner_template(request, template_name):
    partner = which_partner(request)
    return '{0}/{1}'.format(partner.short_name, template_name)

def render_to_response_per_partner(template_name, dictionary, request,
    content_type=settings.DEFAULT_CONTENT_TYPE):

    if request:
        context_instance = RequestContext(request)
    else:
        context_instance = Context(dictionary)
    try:
        return render_to_response(
            per_partner_template(request, template_name),
            dictionary, context_instance, content_type=content_type)
    except TemplateDoesNotExist:
        raise Http404
