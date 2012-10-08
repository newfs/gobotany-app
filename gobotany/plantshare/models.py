from django.db import models
from django.contrib.auth.models import User

SHARING_CHOICES = (
    ('PRIVATE', 'Only PlantShare staff and myself'),
    ('GROUPS', 'My Groups'),
    ('PUBLIC', 'Public - All'),
)

class UserProfile(models.Model):

    user = models.OneToOneField(User)

    display_name = models.CharField(max_length=60, unique=True, blank=True)
    zipcode = models.CharField(max_length=5, blank=True)
    security_question = models.CharField(max_length=100, blank=True)
    security_answer = models.CharField(max_length=100, blank=True)

    # User's profile preferences
    sharing_visibility = models.CharField(blank=False, max_length=7,
        choices=SHARING_CHOICES, default=SHARING_CHOICES[0][0])
    saying = models.CharField(max_length=100, blank=True)


class SharingGroup(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(UserProfile, through='SharingGroupMember',
        related_name='groups')


class SharingGroupMember(models.Model):
    member = models.ForeignKey(UserProfile)
    group = models.ForeignKey(SharingGroup)
    is_owner = models.BooleanField(default=False)


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

    def _parse_location(self):
        """Parse the location field and fill the appropriate detail fields."""
        location = self.location.strip()
        if location:
            if location.find(',') > -1:
                # Location is either city/state or latitude/longitude.
                if location[0].isalpha():
                    # City, state
                    city, state = [x.strip() for x in location.split(',')]
                    self.city = city
                    self.state = state
                else:
                    # Latitude, longitude
                    # TODO: parse more advanced lat/long formats
                    latitude, longitude = [x.strip()
                                           for x in location.split(',')]
                    self.latitude = latitude
                    self.longitude = longitude
            elif (len(location) <= 10 and
                  location[1].isdigit()):  # 2nd char in US/Can. postal codes
                # Postal code
                self.postal_code = location.strip()

    def save(self, *args, **kwargs):
        self._parse_location()
        super(Sighting, self).save(*args, **kwargs)
