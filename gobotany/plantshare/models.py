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

    # Location information is stored as the user entered it, although
    # it is parsed into detail pieces which are also stored.
    location = models.CharField(max_length=255, blank=False)
    location_notes = models.TextField(blank=True)

    # Location details are parsed or derived from the user input.
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=60, blank=True)
    postal_code = models.CharField(max_length=12, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        sighting_id = ''
        if self.id:
            sighting_id = ' %d' % self.id
        created_at = ''
        if self.created:
            created_at = ', %s' % self.created
        return 'Sighting%s: %s at %s (user %d%s)' % (sighting_id,
            self.identification, self.location, self.user.id, created_at)
