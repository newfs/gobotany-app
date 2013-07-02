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

@register.simple_tag
def s_rank_label(code):
    label = code
    if code.startswith('S1'):
        label = 'extremely rare'
    elif code.startswith('S1S2'):
        label = 'extremely rare to rare'
    elif code.startswith('S1S3'):
        label = 'extremely rare to uncommon'
    elif code.startswith('S2'):
        label = 'rare'
    elif code.startswith('S2S3'):
        label = 'rare to uncommon'
    elif code.startswith('S2S4'):
        label = 'rare to fairly widespread'
    elif code.startswith('S3'):
        label = 'uncommon'
    elif code.startswith('S3S4'):
        label = 'uncommon to fairly widespread'
    elif code.startswith('S3S5'):
        label = 'uncommon to widespread'
    elif code.startswith('S4'):
        label = 'fairly widespread'
    elif code.startswith('S5'):
        label = 'widespread'
    elif code == 'SH':
        label = 'historical'
    elif code == 'SNA':
        label = 'not applicable'
    elif code == 'SNR':
        label = 'unranked'
    elif code == 'SU':
        label = 'unrankable'
    elif code == 'SX':
        label = 'extirpated'
    if code.endswith('?'):
        label += ' (uncertain)'
    return label

@register.simple_tag
def endangerment_code_label(code):
    label = code
    if code == '- H':
        label = 'historical'
    elif code == '- WL':
        label = 'Watch List'
    elif code == 'C':
        label = 'concern'
    elif code == 'C*':
        label = 'concern (uncertain)'
    elif code == 'E':
        label = 'endangered'
    elif code == 'FE':
        label = 'federally endangered'
    elif code == 'FT':
        label = 'federally threatened'
    elif code == 'FT/SH':
        label = 'federally threatened/state historical'
    elif code == 'PE':
        label = 'potentially extirpated'
    elif code == 'SC':
        label = 'special concern'
    elif code == 'SC*':
        label = 'special concern, extirpated'
    elif code == 'SE':
        label = 'state endangered'
    elif code == 'SH':
        label = 'state historical'
    elif code == 'SR':
        label = 'state rare'
    elif code == 'ST':
        label = 'state threatened'
    elif code == 'T':
        label = 'threatened'
    return label

# Inclusion tag for formatting a combined title/credit/copyright string
# for use with a photo.
@register.inclusion_tag('gobotany/_photo_credit.html')
def photo_credit(image, image_name):
    return {'image': image, 'image_name': image_name}
