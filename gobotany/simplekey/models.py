from django.db import models


class Collection(models.Model):
    slug = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=50)
    blurb = models.TextField(blank=True)
    contents = models.TextField(blank=True)

    class Meta:
        pass

    def __unicode__(self):
        return u'Collection "%s"' % (self.slug,)
