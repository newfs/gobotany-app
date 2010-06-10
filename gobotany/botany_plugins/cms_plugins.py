from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from gobotany.botany_plugins.models import (TaxonRef,
                                            TaxonImage,
                                            )

class TaxonPlugin(CMSPluginBase):
    model = TaxonRef
    name = _(u'Species')
    render_template = "species.html"

    def render(self, context, instance, placeholder):
        context.update({'taxon':instance.taxon,
                        'object':instance,
                        'placeholder':placeholder})
        return context

class TaxonImagePlugin(CMSPluginBase):
    model = TaxonImage
    name = _(u'Species Image')
    render_template = "species_image.html"

    def render(self, context, instance, placeholder):
        alt = instance.alt or instance.taxon.scientific_name
        context.update({'image':instance,
                        'alt': alt,
                        'placeholder':placeholder})
        return context

plugin_pool.register_plugin(TaxonPlugin)
plugin_pool.register_plugin(TaxonImagePlugin)
