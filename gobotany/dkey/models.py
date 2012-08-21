"""Data model for the dichotomous key."""

from django.db import models

class Page(models.Model):
    chapter = models.TextField(blank=True)
    title = models.TextField(unique=True)
    rank = models.TextField(db_index=True)
    text = models.TextField(blank=True)
    breadcrumb_cache = models.ManyToManyField('Page', related_name='ignore+')

    def __unicode__(self):
        return self.title

class Lead(models.Model):
    page = models.ForeignKey('Page', related_name='leads')
    parent = models.ForeignKey('Lead', related_name='children', null=True)
    letter = models.TextField()
    text = models.TextField()
    goto_page = models.ForeignKey('Page', related_name='leadins', null=True)
    goto_num = models.IntegerField(null=True)
    taxa_cache = models.TextField(blank=True)

    def __unicode__(self):
        return u'{}:{}.{}'.format(self.id, self.letter, self.goto_page_id
                                  or self.goto_num or '')

    def sort_key(self):
        """Turn '12a' into (12, 'a')."""
        return int(self.letter[:-1]), self.letter[-1]

class Figure(models.Model):
    number = models.IntegerField(primary_key=True)
    caption = models.TextField()
