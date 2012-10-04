from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User)

    display_name = models.CharField(max_length=60, unique=True, blank=True)
    zipcode = models.CharField(max_length=5, blank=True)
    security_question = models.CharField(max_length=100, blank=True)
    security_answer = models.CharField(max_length=100, blank=True)


class Sighting(models.Model):
    user = models.ForeignKey(User)

    created = models.DateTimeField(blank=False, auto_now_add=True)
    identification = models.CharField(max_length=120, blank=True)
    title = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    # Location: either address (to be geocoded) or latitude/longitude
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created']

    @property
    def location(self):
        location = self.address
        if self.latitude and self.longitude:
            location = '%f, %f' % (self.latitude, self.longitude)
        return location

    def __unicode__(self):
        sighting_id = ''
        if self.id:
            sighting_id = ' %d' % self.id
        created_at = ''
        if self.created:
            created_at = ', %s' % self.created
        return 'Sighting%s: %s at %s (user %d%s)' % (sighting_id,
            self.identification, self.location, self.user.id, created_at)
