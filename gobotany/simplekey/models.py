from django.db import models
from gobotany.core.models import PileGroup


class Blurb(models.Model):
    name = models.CharField(max_length=50)
    text = models.TextField(blank=True)

    def __unicode__(self):
        return u'Blurb "%s"' % (self.name,)


def get_blurb(name):
    blurbs = Blurb.objects.filter(name=name)
    if blurbs:
        return blurbs[0].text
    return ('[Provide text for this by creating a blurb in the Admin'
            ' interface named %r]' % (name,))


class Page(models.Model):
    number = models.IntegerField(unique=True)
    title = models.CharField(max_length=50)
    pilegroups = models.ManyToManyField(PileGroup, blank=True)
    next_page = models.ForeignKey('Page', blank=True, null=True)

    class Meta:
        pass

    def __unicode__(self):
        return u'Page "%d"' % (self.number,)

    @models.permalink
    def get_absolute_url(self):
        return ('gobotany.simplekey.views.page_view',
                (), { 'number': str(self.number) })
