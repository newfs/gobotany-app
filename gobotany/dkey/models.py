"""Data model for the dichotomous key."""

from django.db import models

class Page(models.Model):
    chapter = models.TextField()
    title = models.TextField(db_index=True, null=True)
    rank = models.TextField(db_index=True)
    text = models.TextField()
    breadcrumb_ids = models.TextField()  # comma-separated like '1,2,3,4,5'
    lead_ids = models.TextField()        # comma-separated like '1,2,3,4,5'

    def __unicode__(self):
        return u'{}:{}'.format(self.id, self.title or 'untitled')

class Lead(models.Model):
    letter = models.TextField()
    text = models.TextField()
    parent = models.ForeignKey('Lead', related_name='children', null=True)
    goto_page = models.ForeignKey('Page', null=True)
    goto_num = models.IntegerField(null=True)

    def __unicode__(self):
        return u'{}:{}.{}'.format(self.id, self.letter, self.goto_page_id
                                  or self.goto_num or '')

class Figure(models.Model):
    number = models.IntegerField(primary_key=True)
    caption = models.TextField()
