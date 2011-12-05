from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from gobotany.core.models import Taxon

class PlantOfTheDayManager(models.Manager):
    """Custom model manager for getting Plant of the Day records by date."""

    def _pick_candidate_plant(self, day_date, partner_name):
        """Pick a candidate Plant of the Day for a given day and partner."""
        candidate_plant = None
        plants = self.filter(last_seen=day_date,
                             partner_short_name=partner_name,
                             include=True)
        if len(plants) > 0:
            candidate_plant = plants[0]
        else:
            # A plant wasn't found for the requested date.
            if day_date > date.today():
                # The requested date is in the future.
                candidate_plant = None
            else:
                # Pick a new Plant of the Day for this date.

                # Try picking a yet-unseen plant at random.
                plants = self.filter(last_seen__isnull=True,
                                     partner_short_name=partner_name,
                                     include=True).order_by('?')
                if len(plants) > 0:
                    candidate_plant = plants[0]
                else:
                    # If none are unseen, pick the one last seen longest ago.
                    plants = self.filter(last_seen__isnull=False,
                                         partner_short_name=partner_name,
                                         include=True).order_by('last_seen')
                    if len(plants) > 0:
                        candidate_plant = plants[0]

        return candidate_plant

    def for_day(self, day_date, partner_name):
        """Return the Plant of the Day for a given day and partner site."""

        plant_for_day = None
        taxon = None

        while not taxon:
            candidate_plant = self._pick_candidate_plant(
                day_date, partner_name)
            if candidate_plant:
                # Make sure this plant still exists in the main database.
                try:
                    taxon = Taxon.objects.get(
                        scientific_name=candidate_plant.scientific_name)
                    plant_for_day = candidate_plant
                except ObjectDoesNotExist:
                    # Disable this plant in the Plant of the Day list,
                    # so it cannot be picked again.
                    candidate_plant.include = False
                    candidate_plant.save()
            else:
                break

        if plant_for_day:
            plant_for_day.last_seen = date.today()
            plant_for_day.save()

        return plant_for_day


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

    # Define a custom model manager.
    get_by_date = PlantOfTheDayManager()

    # Keep the default model manager as well. Because a custom model
    # manager was added, the default manager must be explicitly defined
    # for it to be kept.
    objects = models.Manager()

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
