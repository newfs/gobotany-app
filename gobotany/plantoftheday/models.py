from django.db import models

class PlantOfTheDay(models.Model):
    """A plant that can appear in Plant of the Day."""

    # The name of the plant is not tied to Taxon records. This is so the
    # Plant of the Day list can survive multiple imports of plant
    # characteristics data as is planned for a while after going live.
    scientific_name = models.CharField(max_length=100, db_index=True)
    # Partner site name, not tied to PartnerSite record, for the same
    # reason as above.
    partner_short_name = models.CharField(max_length=30, db_index=True)

    # If a plant is excluded from Plant of the Day by setting this flag
    # in the Django Admin, this will survive multiple imports of plant
    # data as well as rebuilds of the Plant of the Day list.
    include = models.BooleanField(default=True)

    # Date that this plant was last seen in Plant of the Day. Updated
    # each time the plant is featured.
    last_seen = models.DateField(null=True)

    # Date and time that this record was created. Intended only to help
    # maintain the list.
    created = models.DateTimeField(auto_now_add=True)

    # Date and time that this record was last updated, including it being
    # "touched" when rebuilding. Intended only to help maintain the list.
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        # Defining app_label changes the heading in the Admin successfully
        # once tables are created, but interferes with syncdb table
        # creation as an unfortunate side effect.
        # Custom app labels in the Admin will be in a future Django version
        # according to a comment at http://ionelmc.wordpress.com/2011/06/24/
        #app_label = 'Plant of the Day'  # changes heading in Django Admin
        #db_table = 'plantoftheday_plantoftheday'  # needed for the above

        # Django versions prior to 1.4 only honor the first ordering element.
        # https://docs.djangoproject.com/en/dev/ref/models/options/#ordering
        ordering = ['scientific_name', 'partner_short_name']

        unique_together = ('scientific_name', 'partner_short_name')
        verbose_name = 'Plant of the Day'
        verbose_name_plural = 'Plants of the Day'

    def __unicode__(self):
        return '%s (%s)' % (self.scientific_name, self.partner_short_name)
