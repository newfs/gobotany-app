from django.db import models
from gobotany.core.models import Pile


class Blurb(models.Model):
    name = models.CharField(max_length=50)
    text = models.TextField(blank=True)

    def __unicode__(self):
        return u'Blurb "%s"' % (self.name,)


def get_blurb(name):
    blurbs = Blurb.objects.filter(name=name)
    if blurbs:
        return blurbs[0].text
    return ('[Provide text for this paragraph by creating'
            ' a blurb in the Admin interface named %r]' % (name,))
    

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

    def get_children(self):
        """Return the child objects encoded in our ``contents`` field."""
        childlist = []
        for line in self.contents.splitlines():
            fields = line.split(None, 1)
            if len(fields) < 2:
                continue
            kind, pattern = fields
            if kind == 'pile':
                objs = Pile.objects.filter(name=pattern)
            else:
                objs = Collection.objects.filter(slug=pattern)
            if not objs:
                continue
            childlist.append({ 'kind': kind, 'object': objs[0] })
        return childlist
