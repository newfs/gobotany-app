from django.db import models


class Collection(models.Model):
    slug = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=30)
    title = models.CharField(max_length=50)
    contents = models.TextField(blank=True)

    class Meta:
        pass

    def __unicode__(self):
        return u'Collection "%s"' % (self.slug,)

    @models.permalink
    def get_absolute_url(self):
        return ('gobotany.simplekey.views.collection_view',
                (), {'slug': self.slug})
