"""Data model for the dichotomous key."""

from django.db import models

class Page(models.Model):
    chapter = models.TextField()
    title = models.TextField(db_index=True, null=True)
    rank = models.TextField()
    text = models.TextField()
    lead_ids = models.TextField()  # comma-separated like '1,2,3,4,5'

    def __unicode__(self):
        return u'{}:{}'.format(self.id, self.title or 'untitled')

class Lead(models.Model):
    letter = models.TextField()
    text = models.TextField()
    parent = models.ForeignKey('Lead', related_name='children', null=True)
    goto_page = models.ForeignKey('Page', null=True)
    goto_num = models.IntegerField(null=True)

    def __unicode__(self):
        return u'{}:{}.{}'.format(self.id, self.letter, self.target)
