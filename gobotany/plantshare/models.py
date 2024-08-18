import sys
import datetime
import hashlib
import os
import urllib.parse

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage, Storage
from django.db import IntegrityError, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils import timezone

from imagekit import ImageSpec, register
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.utils import get_field_info
from imagekit.processors.resize import ResizeToFit, SmartResize
from PIL import Image
from PIL.ExifTags import TAGS
from storages.backends.s3boto3 import S3Boto3Storage

from gobotany.plantshare.utils import restrictions

VISIBILITY_CHOICES = (
    ('PUBLIC', 'Everyone: public'),
    ('USERS', 'All PlantShare users'),
    #('GROUPS', 'Your Groups'),   # TODO: enable with Groups feature
    ('PRIVATE', 'Only you and PlantShare staff'),
)

PROFILE_VISIBILITY_CHOICES = VISIBILITY_CHOICES[1:]   # No 'public' profiles
DETAILS_DEFAULT_VISIBILITY = [item for item in PROFILE_VISIBILITY_CHOICES
                              if item[0] == 'USERS'][0][0]
LOCATION_DEFAULT_VISIBILITY = [item for item in PROFILE_VISIBILITY_CHOICES
                               if item[0] == 'USERS'][0][0]

SIGHTING_VISIBILITY_CHOICES = VISIBILITY_CHOICES
SIGHTING_DEFAULT_VISIBILITY = [item for item in SIGHTING_VISIBILITY_CHOICES
                               if item[0] == 'PUBLIC'][0][0]

IMAGE_TYPES = (
    ('AVATAR', 'User Avatar'),
    ('SIGHTING', 'Sighting Photo'),
    ('CHECKLIST', 'Checklist Photo'),
    ('QUESTION', 'Question Photo'),
)

DEFAULT_AVATAR_URL = urllib.parse.urljoin(settings.STATIC_URL,
    'images/icons/generic-avatar.png')
DEFAULT_AVATAR_THUMB = urllib.parse.urljoin(settings.STATIC_URL,
    'images/icons/generic-avatar.png')


# PlantShare models

class Location(models.Model):
    """A location as specified by a user in one of several valid ways."""

    # Location information is stored as the user entered it, although
    # it is parsed into detail pieces which are also stored.
    user_input = models.CharField(max_length=255, blank=False)

    # Location details are parsed from the user input or otherwise derived.
    street = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=120, null=True, blank=True)
    state = models.CharField(max_length=60, null=True, blank=True)
    postal_code = models.CharField(max_length=12, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.user_input

    def _parse_user_input(self):
        """Parse the raw input and fill the appropriate detail fields."""
        user_input = self.user_input.strip()
        if user_input:
            if user_input[-1].isalpha():   # last character is a letter
                # Location format is address: street (optional), city, state.
                # (Latitude/longitude is handled elsewhere.)
                parts = [x.strip() for x in user_input.split(',')]
                if len(parts) > 1:
                    self.street = parts[-3] if len(parts) > 2 else None
                    self.city = parts[-2]
                    self.state = parts[-1]

    def save(self, *args, **kwargs):
        self._parse_user_input()
        super(Location, self).save(*args, **kwargs)


class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.PROTECT)

    zipcode = models.CharField(max_length=5, blank=True)
    security_question = models.CharField(max_length=100, blank=True)
    security_answer = models.CharField(max_length=100, blank=True)

    # User's profile details and preferences
    details_visibility = models.CharField(blank=False, max_length=7,
        choices=PROFILE_VISIBILITY_CHOICES,
        default=DETAILS_DEFAULT_VISIBILITY)
    avatar = models.ForeignKey('ScreenedImage', null=True, blank=True,
        on_delete=models.PROTECT)
    display_name = models.CharField(max_length=60, blank=True)
    saying = models.CharField(max_length=100, blank=True)

    # User's profile location and preferences
    location_visibility = models.CharField(blank=False, max_length=7,
        choices=PROFILE_VISIBILITY_CHOICES,
        default=LOCATION_DEFAULT_VISIBILITY)
    location = models.ForeignKey(Location, null=True, blank=True,
        on_delete=models.PROTECT)

    def __str__(self):
        return '%s (%s)' % (self.display_name, self.user.username)

    @classmethod
    def default_avatar_image(cls):
        return {
            'url': DEFAULT_AVATAR_URL,
            'thumb_url': DEFAULT_AVATAR_THUMB,
        }

    def private_avatar_image(self):
        '''Convenience method that will return the user's latest uploaded
        avatar, whether or not it has been approved by staff.  This should
        ONLY appear to the user himself.
        '''
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
        '''Convenience method that will return the user's current avatar.
        This will display only a pre-screened, approved avatar, or the default
        "empty" avatar if the user has no approved avatar.  This should be
        used in any views displayed to anyone other than this user.
        '''
        if self.avatar:
            avatar_info = {
                'url': self.avatar.image.url,
                'thumb_url': self.avatar.thumb.url,
            }
        else:
            avatar_info = self.__class__.default_avatar_image()

        return avatar_info

    @property
    def checklists(self):
        """Retrieve the list of all checklists this user has created
        or has been added as a collaborator on, including those editable due
        to Pod membership.
        """
        return Checklist.objects.filter(collaborators__members=self)

    def get_user_pod(self):
        return self.pods.get(podmembership__is_self_pod=True)

    def user_display_name(self):
        """Return the basic display name for a user, which is either the
        chosen display name or, if no display name is set, the username.
        """
        display_name = self.user.username
        if self.display_name:
            display_name = self.display_name
        return display_name

    def unique_user_display_name(self):
        """Return the unique display name for a user, which is either the
        chosen display name or, if no display name is set, their username.
        If the display name is not unique, that is, another user has the same
        one, then add the username in parentheses after the display name.
        """
        display_name = self.user.username
        if self.display_name:
            display_name = self.display_name
            num_users_with_name = UserProfile.objects.filter(
                display_name=display_name).count()
            if num_users_with_name > 1:
                display_name = '%s (%s)' % (display_name, self.user.username)
        return display_name

    def user_first_name(self):
        """Return the first part of the user's display name, if defined.
        Otherwise, return the username.
        """
        return self.user_display_name().split(' ')[0]

@receiver(post_save, sender=User, dispatch_uid='create_profile_for_user')
def create_user_profile(sender, **kwargs):
    user = kwargs['instance']
    created = kwargs['created']
    # Only when a user is first created, we should create his UserProfile
    # and his personal Pod.
    if created:
        profile = UserProfile(user=user)
        profile.save()
        user_pod = Pod(name=user.username)
        user_pod.save()
        membership = PodMembership(member=profile, pod=user_pod,
            is_owner=True, is_self_pod=True)
        membership.save()


class SightingManager(models.Manager):
    def public(self):
        """Return sightings marked for public view."""
        return self.filter(visibility='PUBLIC')


class Sighting(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    created = models.DateTimeField(blank=False)
    identification = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    location = models.ForeignKey(Location, null=True,
        on_delete=models.PROTECT)
    location_notes = models.TextField(blank=True)

    photos = models.ManyToManyField('ScreenedImage', blank=True)

    visibility = models.CharField(blank=False, max_length=7,
        choices=SIGHTING_VISIBILITY_CHOICES,
        default=SIGHTING_DEFAULT_VISIBILITY)

    # Add field for administrators indicating "flagged for review" if True.
    flagged = models.BooleanField(default=False)

    # Add field for administrators indicating approval of a flagged sighting.
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']
        verbose_name = 'sighting'
        verbose_name_plural = 'sightings'

    def __str__(self):
        sighting_id = ''
        if self.id:
            sighting_id = ' %d' % self.id
        created_at = ''
        if self.created:
            created_at = ', %s' % self.created
        return 'Sighting%s: %s at %s (user %d%s)' % (sighting_id,
            self.identification, self.location, self.user.id, created_at)

    def private_photos(self):
        '''Return photos which have either not been screened, or are screened
        and approved. This should only be used on views shown only to the user
        who uploaded the photos.
        '''
        return self.photos.exclude(
                screened__isnull=False,
                is_approved=False
                ).exclude(deleted=True).exclude(orphaned=True)

    def approved_photos(self):
        '''Return only photos which have been screened and approved.
        Use this method for any view where someone other than the owner
        will see these photos.
        '''
        return self.photos.filter(is_approved=True, deleted=False,
                orphaned=False)

    objects = SightingManager()


# Storage location for uploaded images depends on environment.

if not settings.IN_PRODUCTION:
    # Local development environment upload
    upload_storage = FileSystemStorage(
            location=os.path.join(settings.MEDIA_ROOT, 'upload_images'),
            base_url=urllib.parse.urljoin(settings.MEDIA_URL, 'upload_images/'))
elif settings.IS_AWS_AUTHENTICATED:
    # Direct upload to S3
    upload_storage = S3Boto3Storage(location='upload_images',
            bucket=getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'newfs'))
else:
    # Direct upload to S3
    upload_storage = Storage()


def rename_image_by_type(instance, filename):
    user_name = instance.uploaded_by.username.lower()
    image_type = instance.image_type.lower()

    # Create and update a hash object for getting a unique name.
    md5 = hashlib.md5()
    md5.update(filename.encode('utf-8'))
    md5.update(user_name.encode('utf-8'))
    md5.update(image_type.encode('utf-8'))
    md5.update(str(datetime.datetime.now()).encode('utf-8'))

    new_name = '{0}_{1}.jpg'.format(user_name, md5.hexdigest())
    return os.path.join(image_type, new_name)


class ExifGpsExtractor(object):
    """ Custom django-imagekit image processor to extract GPS coordinates
    from original image.
    This is a little non-standard in that it requires an object
    of some sort with 'latitude' and 'longitude' attributes on which to store
    the extracted data. """
    def __init__(self, target_object):
        self.target_object = target_object

    def process(self, image):
        self._extract_gps_data(image)
        return image

    def _get_dms(self, exif_data):
        degrees = float(exif_data[0])
        minutes = float(exif_data[1])
        seconds = float(exif_data[2])
        return (degrees, minutes, seconds)

    def _get_coordinate(self, degrees, minutes, seconds):
        fractional_degrees = ((minutes * 60) + seconds) / 3600
        coordinate = degrees + fractional_degrees
        return coordinate

    def _extract_gps_data(self, img):
        # Extract any GPS coordinates in the image metadata and save them
        # in the database before the data are automatically erased due to
        # the ProcessedImageField image that gets resized and saved.
        DECIMAL_PLACES = 7

        # These are tag ids defined by the EXIF Specification
        EXIF_GPSLATITUDE = 2
        EXIF_GPSLATITUDEREF = 1
        EXIF_GPSLONGITUDE = 4
        EXIF_GPSLONGITUDEREF = 3

        exif = None
        try:
            exif = img._getexif()
        except AttributeError:
            pass
        if exif:
            tagged_exif = {
                TAGS[k]: v for k, v in list(exif.items()) if k in TAGS
            }
            gps_info = tagged_exif.get('GPSInfo', {})
            available_tags = set(gps_info.keys())
            required_tags = set((EXIF_GPSLATITUDE, EXIF_GPSLATITUDEREF,
                    EXIF_GPSLONGITUDE, EXIF_GPSLONGITUDEREF))
            if gps_info and required_tags <= available_tags:
                # Get latitude.
                degrees, minutes, seconds = self._get_dms(
                    gps_info[EXIF_GPSLATITUDE])
                latitude = self._get_coordinate(degrees, minutes, seconds)
                direction = gps_info[EXIF_GPSLATITUDEREF]
                if direction.upper() == 'S':
                    latitude = latitude * -1
                latitude = round(latitude, DECIMAL_PLACES)
                ### debugging
                print(('_extract_gps_data: latitude:', latitude))
                print('_extract_gps_data: about to try to set lat./long.s')
                print(('self:', self))
                print(('selt.target_object:', self.target_object))
                ###
                try:
                    self.target_object.latitude = latitude
                except AttributeError:
                    print(('cannot set latitude on target_object:', \
                        type(self.target_object)))
                finally:
                    # Get longitude.
                    degrees, minutes, seconds = self._get_dms(
                        gps_info[EXIF_GPSLONGITUDE])
                    longitude = self._get_coordinate(degrees, minutes,
                        seconds)
                    direction = gps_info[EXIF_GPSLONGITUDEREF]
                    if direction.upper() == 'W':
                        longitude = longitude * -1
                    longitude = round(longitude, DECIMAL_PLACES)
                    print(('_extract_gps_data: longitude:', longitude))
                    try:
                        self.target_object.longitude = longitude
                    except AttributeError:
                        print(('cannot set longitude on target_object:', \
                            type(self.target_object)))


class PlantshareGpsImage(ImageSpec):
    """ Custom ImageKit ImageSpec to extract GPS data from an image and
    resize it appropriately.
    """
    format = 'JPEG'
    options = {'quality': 60}

    @property
    def processors(self):
        """ Dynamically create the list of image processors using the model
        instance. """
        # August 2018: found that this code no longer seems to be
        # able to produce a model instance as it must have in the past.
        # When this happens, the ExifGpsExtractor image processor below
        # cannot save any extracted latitude or longitude coordinates.
        # TODO: debug and resolve, or else extract and save coordinates
        # another way (such as client side).
        print(('processors(): self.source:', self.source))
        print(('processors(): type(self.source):', type(self.source)))
        instance, field_name = get_field_info(self.source)
        print(('processors() instance:', instance))
        print(('processors() field_name:', field_name))

        return [
            ExifGpsExtractor(instance),
            ResizeToFit(1000, 1000, False),
        ]


register.generator('plantshare:screenedimage:plantsharegpsimage',
        PlantshareGpsImage)


class ScreenedImage(models.Model):
    image = ProcessedImageField(upload_to=rename_image_by_type,
                storage=upload_storage,
                spec_id='plantshare:screenedimage:plantsharegpsimage')
    thumb = ImageSpecField(source='image', format='JPEG',
                options={'quality': 60},
                processors=[ResizeToFit(128, 128, upscale=True)])

    # Add another thumbnail, cropped and centered with consistent
    # dimensions regardless of portrait or landscape orientation.
    thumb_cropped = ImageSpecField(source='image', format='JPEG',
                options={'quality': 60},
                processors=[SmartResize(183, 149, upscale=True)])

    uploaded = models.DateTimeField(blank=False, auto_now_add=True)
    uploaded_by = models.ForeignKey(User, null=False,
        related_name='images_uploaded', on_delete=models.PROTECT)

    image_type = models.CharField(blank=True, max_length=10,
                                  choices=IMAGE_TYPES)

    # If GPS coordinates exist in the image metadata, they are recorded 
    # before storing the image, which strips metadata during processing.
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    screened = models.DateTimeField(null=True)
    screened_by = models.ForeignKey(User, null=True,
        related_name='images_approved', on_delete=models.PROTECT)
    is_approved = models.BooleanField(default=False)

    # Flag true if the image has been orphaned (old avatars, user-deleted
    # avatars, deleted sighting photos)
    orphaned = models.BooleanField(default=False)

    # Flag true if the user or staff has chosen to delete this image.  This
    # indicates that the image binary itself has been removed from storage.
    deleted = models.BooleanField(default=False)


class QuestionManager(models.Manager):
    def answered(self):
        """Return questions with an answer approved for publication."""
        return self.filter(approved=True).exclude(
            answer__isnull=True).exclude(answer__exact='')


class Question(models.Model):
    question = models.CharField(max_length=500, blank=False)
    images = models.ManyToManyField('ScreenedImage', blank=True)
    answer = models.CharField(max_length=3000, blank=True)
    asked = models.DateTimeField(blank=False, auto_now_add=True)
    asked_by = models.ForeignKey(User, blank=False,
        related_name='questions_asked', on_delete=models.PROTECT)

    approved = models.BooleanField(default=False)

    # The "answered" date is a non-editable field that automatically fills
    # in when an answered question is approved in the Admin for publication.
    answered = models.DateTimeField(null=True, editable=False)

    class Meta:
        verbose_name = 'question'
        verbose_name_plural = 'questions'

    def __str__(self):
        return '%d: %s' % (self.id, self.question)

    def asked_date(self):
        """Return a version of the 'asked' field that just has the date."""
        return self.asked.strftime('%Y-%m-%d')

    def notify_user(self):
        """Notify the user that the question has been answered on the site."""
        user_name = self.asked_by.username
        try:
            user_profile = UserProfile.objects.get(user=self.asked_by)
            user_name = user_profile.user_first_name()
        except ObjectDoesNotExist:
            pass
        site = Site.objects.get_current()
        context = {
            'user_name': user_name,
            'site': site,
            'question_id': self.id,
            'question': self.question,
            'year': self.answered.year,
            'in_production': settings.IN_PRODUCTION,
        }
        subject = render_to_string('question_answered_email_subject.txt')
        subject = ''.join(subject.splitlines())   # remove newlines
        message = render_to_string('question_answered_email.txt', context)
        self.asked_by.email_user(subject, message)

    def save(self):
        # Auto-populate the "answered" date the first time a question is
        # approved in the the Admin, and notify the user by email.
        if self.answer and self.approved == True and not self.answered:
            now = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
            self.answered = now
            self.notify_user()

        # If the question is answered or approved, then any attached images
        # are implicitly approved (otherwise the Admin user would just delete
        # the question), so set the images as approved.
        if self.answer or self.approved == True:
            for image in self.images.all():
                image.is_approved = True
                image.save()

        super(Question, self).save()

    objects = QuestionManager()


class Pod(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(UserProfile, through='PodMembership',
            related_name='pods')

    def get_owner(self):
        return self.members.get(podmembership__is_owner=True)


class PodMembership(models.Model):
    member = models.ForeignKey(UserProfile, on_delete=models.PROTECT)
    pod = models.ForeignKey(Pod, on_delete=models.PROTECT)
    # Is this the pod owner?
    is_owner = models.BooleanField(default=False)
    # Is this this user's personal pod (for sharing purposes)
    is_self_pod = models.BooleanField(default=False)


class Checklist(models.Model):
    """A container of checklist items which represent plants to search for."""
    name = models.CharField(max_length=100)
    comments = models.TextField(blank=True)

    """Pods that can view and update this actual Checklist instance.
    Any members of these Pods can collaborate on adding or editing items
    on this Checklist. If the owner flag is set, the Pod members may also
    delete items."""
    collaborators = models.ManyToManyField('Pod', related_name='checklists',
            through='ChecklistCollaborator')

    @property
    def owner(self):
        return self.collaborators.get(checklistcollaborator__is_owner=True)

    def copy_to_user(self, user):
        """Send a copy of this checklist to another user. The user will
        have full privledges to edit the copy as if they created it. The
        list of collaborators will be cleared in the copy."""
        user_pod = user.profile.get_user_pod()
        checklist_copy = self
        checklist_copy.pk = None
        checklist_copy.collaborators.clear()
        checklist_copy.save()

        # Copy all the checklist entries, but don't save the checked
        # state or any of the optional details - the new checklist
        # should be "blank"
        copied_entries = []
        for entry in self.entries:
            item_copy = ChecklistEntry(plant_name=entry.plant_name,
                    checklist=checklist_copy)
            copied_entries.append(item_copy)

        ChecklistEntry.objects.bulk_create(copied_entries)

        # Assign ownership of the new checklist to the user
        ownership = ChecklistCollaborator(collaborator=user_pod,
                checklist=checklist_copy, is_owner=True)
        ownership.save()

    def share_to_user(self, user):
        """Allow another user to collaborate and edit this checklist"""
        user_pod = user.profile.get_user_pod()
        user_access = ChecklistCollaborator(collaborator=user_pod,
                checklist=self, is_owner=False)
        user_access.save()

    def share_to_pod(self, pod):
        """Allow members of a pod to collaborate and edit this checklist"""
        pod_access = ChecklistCollaborator(collaborator=pod,
                checklist=self, is_owner=False)
        pod_access.save()


class ChecklistEntry(models.Model):
    """An individual entry on a checklist. An entry on a checklist represents
    a taxon to be searched for, and which can later be "checked off" when
    found."""
    checklist = models.ForeignKey(Checklist, related_name='entries',
        on_delete=models.PROTECT)

    plant_name = models.CharField(max_length=100, blank=False)

    is_checked = models.BooleanField(default=False)
    plant_photo = models.ForeignKey(ScreenedImage, null=True, blank=True,
        on_delete=models.PROTECT)
    location = models.CharField(max_length=100, blank=True)

    date_found = models.DateTimeField(null=True, blank=True)
    date_posted = models.DateTimeField(null=True, blank=True)

    note = models.TextField(blank=True)


class ChecklistCollaborator(models.Model):
    collaborator = models.ForeignKey(Pod, on_delete=models.PROTECT)
    checklist = models.ForeignKey(Checklist, on_delete=models.PROTECT)

    is_owner = models.BooleanField(default=False)
