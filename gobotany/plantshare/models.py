import datetime
import os
import urlparse
import hashlib

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import Storage, FileSystemStorage

from storages.backends.s3boto import S3BotoStorage
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors.resize import ResizeToFit

SHARING_CHOICES = (
    ('PRIVATE', 'Only PlantShare staff and myself'),
    ('GROUPS', 'My Groups'),
    ('PUBLIC', 'Public - All'),
)

IMAGE_TYPES = (
    ('AVATAR', 'User Avatar'),
    ('SIGHTING', 'Sighting Photo'),
)

DEFAULT_AVATAR_URL = urlparse.urljoin(settings.STATIC_URL,
    'images/icons/avatar-scary-placeholder.png')
DEFAULT_AVATAR_THUMB = urlparse.urljoin(settings.STATIC_URL,
    'images/icons/avatar-scary-placeholder.png')

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
                    # City, state (lat/long handled elsewhere)
                    city, state = [x.strip() for x in user_input.split(',')]
                    self.city = city
                    self.state = state
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

    # User's location preferences
    location_visibility = models.CharField(blank=False, max_length=7,
        choices=SHARING_CHOICES, default=SHARING_CHOICES[0][0])
    location = models.ForeignKey(Location, null=True, blank=True)

    avatar = models.ForeignKey('ScreenedImage', null=True, blank=True)

    @classmethod
    def default_avatar_image(cls):
        return {
            'url': DEFAULT_AVATAR_URL,
            'thumb_url': DEFAULT_AVATAR_THUMB,
        }

    def private_avatar_image(self):
        ''' Convenience method that will return the user's latest uploaded avatar,
        whether or not it has been approved by staff.  This should ONLY appear to
        the user himself. '''
        latest_avatars = ScreenedImage.objects.filter(
                uploaded_by=self.user, 
                image_type='AVATAR',
                deleted=False,
                orphaned=False
                ).order_by('-uploaded')
        if len(latest_avatars) > 0:
            this_avatar = latest_avatars[0]
            avatar_info = {
                'url': this_avatar.image.url,
                'thumb_url': this_avatar.thumb.url,
            }
        else:
            avatar_info = self.__class__.default_avatar_image()

        return avatar_info
    
    def public_avatar_image(self):
        ''' Convenience method that will return the user's current avatar. This will
        display only a pre-screened, approved avatar, or the default "empty" avatar
        if the user has no approved avatar.  This should be used in any views
        displayed to anyone other than this user.'''
        if self.avatar:
            avatar_info = {
                'url': self.avatar.image.url,
                'thumb_url': self.avatar.thumb.url,
            }
        else:
            avatar_info = self.__class__.default_avatar_image()

        return avatar_info


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
    # TODO: delete title field once confirmed it will not be needed
    title = models.CharField(max_length=120, blank=False)
    notes = models.TextField(blank=True)

    location = models.ForeignKey(Location, null=True)
    location_notes = models.TextField(blank=True)

    photos = models.ManyToManyField('ScreenedImage', null=True, blank=True)

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

    def private_photos(self):
        ''' Return photos which have either not been screened, or are screened
        and approved.  This should only be used on views shown only to the user
        who uploaded the photos. '''
        return self.photos.exclude(
                screened__isnull=False,
                is_approved=False
                ).exclude(deleted=True).exclude(orphaned=True)

    def approved_photos(self):
        ''' Return only photos which have been screened and approved.
        Use this method for any view where someone other than the owner
        will see these photos.'''
        return self.photos.filter(is_approved=True, deleted=False,
                orphaned=False)

if settings.DEBUG:
    # Local, debug upload
    upload_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'upload_images'),
            base_url=urlparse.urljoin(settings.MEDIA_URL, 'upload_images/'))
elif settings.IS_AWS_AUTHENTICATED:
    # Direct upload to S3
    upload_storage = S3BotoStorage(location='/upload_images',
            bucket='newfs')
else:
    # Direct upload to S3
    upload_storage = Storage()

def rename_image_by_type(instance, filename):
    # Create a checksum so we have a unique name
    md5 = hashlib.md5()
    f = instance.image
    if f.multiple_chunks():
        for chunk in f.chunks():
            md5.update(chunk)
    else:
        md5.update(f.read())

    new_name = '{0}_{1}.png'.format(instance.uploaded_by.username.lower(),
            md5.hexdigest())

    return os.path.join(instance.image_type.lower(), new_name)


class ScreenedImage(models.Model):
    image = ProcessedImageField(upload_to=rename_image_by_type, 
                storage=upload_storage, format='PNG', 
                processors=[ResizeToFit(1000, 1000)])
    thumb = ImageSpecField(image_field='image', storage=upload_storage, format='PNG',
                processors=[ResizeToFit(128, 128, upscale=True)]) 

    uploaded = models.DateTimeField(blank=False, auto_now_add=True)
    uploaded_by = models.ForeignKey(User, null=False, related_name='images_uploaded')

    image_type = models.CharField(blank=True, max_length=10,
            choices=IMAGE_TYPES)

    screened = models.DateTimeField(null=True)
    screened_by = models.ForeignKey(User, null=True, related_name='images_approved')
    is_approved = models.BooleanField(default=False)

    # Flag true if the image has been orphaned (old avatars, user-deleted avatars,
    # deleted sighting photos)
    orphaned = models.BooleanField(default=False)

    # Flag true if the user or staff has chosen to delete this image.  This
    # indicates that the image binary itself has been removed from storage.
    deleted = models.BooleanField(default=False)


class Question(models.Model):
    question = models.CharField(max_length=300, blank=False)
    answer = models.CharField(max_length=3000, blank=True)
    category = models.CharField(max_length=120, blank=False)
    asked = models.DateTimeField(blank=False, auto_now_add=True)
    asked_by = models.ForeignKey(User, blank=False,
                                 related_name='questions_asked')
    answered = models.DateTimeField(null=True, editable=False)
    duplicate_of = models.ForeignKey('Question', blank=True, null=True,
                                     related_name='duplicates')

    def __unicode__(self):
        return '%d: %s' % (self.id, self.question)

    def save(self):
        # Auto-populate the "answered" date upon answering a question.
        if self.answer:
            self.answered = datetime.date.today()
        super(Question, self).save()
