import os
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage

from storages.backends.s3boto import S3BotoStorage

SHARING_CHOICES = (
    ('PRIVATE', 'Only PlantShare staff and myself'),
    ('GROUPS', 'My Groups'),
    ('PUBLIC', 'Public - All'),
)

IMAGE_TYPES = (
    ('AVATAR', 'User Avatar'),
    ('SIGHTING', 'Sighting Photo'),
)

class Location(models.Model):
    """A location as specified by a user in one of several valid ways."""

    # Location information is stored as the user entered it, although
    # it is parsed into detail pieces which are also stored.
    user_input = models.CharField(max_length=255, blank=False)

    # Location details are parsed from the user input or otherwise derived.
    city = models.CharField(max_length=120, null=True, blank=True)
    state = models.CharField(max_length=60, null=True, blank=True)
    postal_code = models.CharField(max_length=12, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.user_input

    def _parse_user_input(self):
        """Parse the raw input and fill the appropriate detail fields."""
        user_input = self.user_input.strip()
        if user_input:
            if user_input.find(',') > -1:
                # Location is either city/state or latitude/longitude.
                if user_input[0].isalpha():
                    # City, state
                    city, state = [x.strip() for x in user_input.split(',')]
                    self.city = city
                    self.state = state
                else:
                    # Latitude, longitude
                    # TODO: parse more advanced lat/long formats
                    latitude, longitude = [x.strip()
                                           for x in user_input.split(',')]
                    self.latitude = latitude
                    self.longitude = longitude
            elif (len(user_input) <= 10 and
                  user_input[1].isdigit()): # 2nd char in US/Can. postal codes
                # Postal code
                self.postal_code = user_input.strip()

    def save(self, *args, **kwargs):
        self._parse_user_input()
        super(Location, self).save(*args, **kwargs)


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
    title = models.CharField(max_length=120, blank=False)
    notes = models.TextField(blank=True)

    location = models.ForeignKey(Location, null=True)
    location_notes = models.TextField(blank=True)

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


if settings.DEBUG:
    # Local, debug upload
    upload_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'upload_images'))
else:
    # Direct upload to S3
    upload_storage = S3BotoStorage(location='/upload_images')

class ScreenedImage(models.Model):
    image = models.ImageField(upload_to='.', storage=upload_storage)

    uploaded = models.DateTimeField(blank=False, auto_now_add=True)
    uploaded_by = models.ForeignKey(User, null=False, related_name='images_uploaded')

    image_type = models.CharField(blank=True, max_length=10,
            choices=IMAGE_TYPES)

    screened = models.DateTimeField(blank=True)
    screened_by = models.ForeignKey(User, null=True, related_name='images_approved')
    is_approved = models.BooleanField(default=False)
