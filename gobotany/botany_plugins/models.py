from django.db import models
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from cms.models import CMSPlugin
from cms.models import Page
from gobotany import models as botany_models

# XXX: These should probably not be hard-coded
IMAGE_TYPES = [('overall', _(u'Overall')),
               ('leaf', _(u'Leaf')),
               ('stem', _(u'Stem')),
               ('branch', _(u'Branch')),
               ('cone', _(u'Cone')),
               ]

class TaxonRef(CMSPlugin):
    """Display a taxon object in a CMS page"""
    taxon = models.ForeignKey(botany_models.Taxon,
                              verbose_name=_(u'species'))

class TaxonImage(CMSPlugin):
    image = models.ImageField(_('plant image'),
                              upload_to='taxon_images')
    taxon = models.ForeignKey(botany_models.Taxon,
                              verbose_name=_(u'species'),
                              blank=True,
                              null=True)
    alt = models.CharField(max_length=100,
                           verbose_name=_(u'alt text'),
                           blank=True)
    canonical = models.BooleanField(default=False)
    image_type = models.CharField(max_length=30,
                                  choices=IMAGE_TYPES,
                                  verbose_name=_(u'image type'),
                                  blank=False)
    description = models.TextField(verbose_name=_(u'description'),
                                   blank=True)

    def clean(self):
        """Some extra validation checks"""
        # If no taxon was provided, then use the taxon from the page
        # if available
        if not self.taxon:
            _set_taxon_from_placeholder(self)

        # Ensure there is only one canonical image per type for the species
        if self.canonical:
            existing = TaxonImage.objects.filter(canonical=True,
                                           image_type=self.image_type,
                                           taxon=self.taxon).exclude(id=self.id)
            if existing:
                raise ValidationError('There is already a canonical %s image '
                                      'for %s.'%(self.image_type,
                                                 self.taxon.scientific_name))

    def save(self, *args, **kwargs):
        """The placeholder may not have been ready when clean was run, if
        the image was the first entry.  In that case, we run clean again.
        Unfortunately, this results in an ugly error if validation fails."""
        if not self.taxon:
            self.clean()
        super(TaxonImage, self).save(*args, **kwargs)


def _set_taxon_from_placeholder(plugin):
    """Checks to see if the current placeholder has a single
    associated taxon page, otherwise raises an error"""
    if plugin.placeholder:
        try:
            page = Page.objects.get(placeholders=plugin.placeholder)
            species = botany_models.Taxon.objects.get(
                taxonref__placeholder__page=page)
            plugin.taxon = species
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            raise ValidationError('Could not find species for this page, '
                                  'please select species manually, or add '
                                  'exactly one to this page')
