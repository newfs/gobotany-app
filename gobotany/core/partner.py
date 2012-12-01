"""Routines that help adapt Go Botany sites for different partners."""

from gobotany.core.models import PartnerSite

def which_partner(request):
    """Determine which partner site is being viewed."""
    short_name = request.get_host().split('.', 1)[0]  # the 'foo' of 'foo.com'
    possibilities = (short_name, 'gobotany')
    matches = list(PartnerSite.objects.filter(short_name__in=(possibilities)))
    if len(matches) > 1 and matches[1].short_name == short_name:
        return matches[1]
    elif len(matches):
        return matches[0]
    return None

def partner_short_name(request):
    partner = which_partner(request)
    if partner is None:
        return None
    return partner.short_name
