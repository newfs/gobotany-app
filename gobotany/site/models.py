import datetime

from django.db import models
from django.dispatch import receiver

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

class Document(models.Model):
    """A document file uploaded through the Admin that can be published
    on the site.
    """
    title = models.CharField(max_length=100, null=True, blank=True)
    last_updated_at = models.DateTimeField(auto_now_add=True)
    upload = models.FileField(upload_to='docs/')
    
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