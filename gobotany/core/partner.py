"""Routines that help adapt Go Botany sites for different partners."""

from gobotany.core.models import PartnerSite

def which_partner(request):
    """Determine which partner site is being viewed."""
    short_name = request.get_host().split('.', 1)[0]  # the 'foo' of 'foo.com'
    partner_matches = list(PartnerSite.objects.filter(short_name=short_name))
    if partner_matches:
        return partner_matches[0]
    return None
