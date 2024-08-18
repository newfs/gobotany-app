import datetime
import os
import urllib.parse

from django.conf import settings
from django.core.files.storage import FileSystemStorage, Storage
from django.db import models
from django.dispatch import receiver

from storages.backends.s3boto3 import S3Boto3Storage

# Models for data that pertain to the overall Go Botany site, but not
# specifically plant data (the Django app "core") nor solely for
# individual site features (such as the Django apps "dkey", "simplekey",
# etc.).

class PlantNameSuggestion(models.Model):
    """An index of plant names for auto-suggesting plant name input."""
    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):
        return '%s' % self.name

class SearchSuggestion(models.Model):
    """An index of terms for auto-suggesting searches."""
    term = models.CharField(max_length=150, unique=True, db_index=True)

    def __str__(self):
        return '%s' % self.term

    def save(self, *args, **kw):
        """Store all search suggestion terms in lower case."""
        self.term = self.term.lower()
        super(SearchSuggestion, self).save(*args, **kw)


# As with screened images elsewhere, storage location for documents
# depends on environment: use file system for local development, but
# S3 for Production and similar (Dev) environments.

if not settings.IN_PRODUCTION:
    # Local development environment upload
    docs_upload_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'docs'),
        base_url=urllib.parse.urljoin(settings.MEDIA_URL, 'docs/'))
elif settings.IS_AWS_AUTHENTICATED:
    # Direct upload to S3
    docs_upload_storage = S3Boto3Storage(location='docs',
        bucket=getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'newfs'))
else:
    # Direct upload to S3
    docs_upload_storage = Storage()


class Document(models.Model):
    """A document file uploaded through the Admin that can be published
    on the site.
    """
    title = models.CharField(max_length=100, null=True, blank=True)
    last_updated_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(storage=docs_upload_storage)
    
@receiver(models.signals.pre_save, sender=Document)
def update_title_date(sender, instance, using, **kwargs):
    # If there's no document title saved, get the name from the file.
    if instance.title is None:
        title = instance.upload.name
        if title:
            instance.title = title
    # Each time the record is updated, update the date.
    instance.last_updated_at = datetime.datetime.now()

@receiver(models.signals.post_delete, sender=Document)
def remove_file_from_storage(sender, instance, using, **kwargs):
    # When the record is deleted, also delete the uploaded file.
    instance.upload.delete(save=False)


class Highlight(models.Model):
    """A home page highlight to tell about a recently added Update.

    A single active Highlight record, the most recent, shows on the page.

    Intended to be turned on only temporarily, when a home page notice
    is needed, but not to be present all the time on the home page.
    """
    note = models.TextField()
    active = models.BooleanField(default=False)


class Update(models.Model):
    """An entry for an Updates page regarding site (data) improvements."""
    date = models.DateField()
    description = models.TextField()
    # The family field is currently not in use and may be removed in a
    # future release.
    family = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-date']