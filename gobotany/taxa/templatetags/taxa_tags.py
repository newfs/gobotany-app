"""Taxa-app template tags and filters."""

from django import template

from gobotany.core.models import PartnerSite
from gobotany.core.partner import which_partner

register = template.Library()

@register.tag
def lookalike_item(parser, token):
    """Return a plant lookalike ("sometimes confused with") item, hyperlinked
    only if the plant is found in the current "partner" site.
    """
    tag_name, scientific_name = token.split_contents()
    return LookalikeItemNode(scientific_name)

class LookalikeItemNode(template.Node):
    def __init__(self, scientific_name):
        self.scientific_name = template.Variable(scientific_name)

    def render(self, context):
        scientific_name = self.scientific_name.resolve(context)
        partner = which_partner(context['request'])

        partner_site = PartnerSite.objects.get(short_name=partner)
        partner_has_species = partner_site.has_species(scientific_name)

        try:
            href = ''
            if partner_has_species:
                href = 'href="/species/%s/"' % \
                       scientific_name.lower().replace(' ', '/')
            html = '<a %s><i>%s</i></a>' % (href, scientific_name)
            return html
        except template.VariableDoesNotExist:
            return ''


# Inclusion tag for formatting a combined title/credit/copyright string
# for use with a photo.
@register.inclusion_tag('gobotany/_photo_credit.html')
def photo_credit(image, image_name):
    return {'image': image, 'image_name': image_name}
