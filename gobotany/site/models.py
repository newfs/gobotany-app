from django.db import models

# Models for data that pertain to the overall Go Botany site, but not
# specifically plant data (the Django app "core") nor solely for
# individual site features (such as the Django apps "dkey", "simplekey",
# etc.).

# TODO: move some models from the "simplekey" app to this one

class PlantNameSuggestion(models.Model):
    """An index of plant names for auto-suggesting plant name input."""
    name = models.CharField(max_length=150, unique=True, db_index=True)

    def __unicode__(self):
        return u'%s' % self.name
