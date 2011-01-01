from django.db import models
from gobotany.core.models import GlossaryTerm, PileGroup


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


# Note: The motivation for creating the following classes was to organize
# information for the Help and Glossary pages in order to build Haystack
# search engine indexes for them.

class Video(models.Model):
    """Information on YouTube videos used for help on the site."""
    title = models.CharField(max_length=100)
    youtube_id = models.CharField(max_length=20)
    # May want to fetch additional metadata from YouTube and store it.
    # Can retrieve Atom XML with a GET request, e.g.,
    # http://gdata.youtube.com/feeds/api/videos/LQ-jv8g1YVI?v=2
    # See docs: http://bit.ly/c1vHUz

    def __unicode__(self):
        return u'%s: %s' % (self.title, self.youtube_id)


class HelpPage(models.Model):
    """Outline of the contents of a Help page."""
    title = models.CharField(max_length=100)
    url_path = models.CharField(max_length=100)
    blurbs = models.ManyToManyField(Blurb)
    videos = models.ManyToManyField(Video)
    
    class Meta:
        verbose_name_plural = 'help pages'

    def __unicode__(self):
        return u'%s' % self.title


class GlossaryHelpPage(models.Model):
    """A Help page that lists glossary terms for a letter (or number).
       
       (Do not inherit from HelpPage here, in order to keep records separate
       for search engine indexing.)
    """
    title = models.CharField(max_length=100)
    url_path = models.CharField(max_length=100)
    letter = models.CharField(max_length=1)
    terms = models.ManyToManyField(GlossaryTerm)

    class Meta:
        verbose_name_plural = 'glossary help pages'

    def __unicode__(self):
        return u'%s' % self.title


class SearchSuggestion(models.Model):
    """An index of terms for auto-suggesting searches."""
    term = models.CharField(max_length=150, unique=True, db_index=True)

    def __unicode__(self):
        return u'%s' % self.term
