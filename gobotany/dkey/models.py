"""Data model for the dichotomous key."""

from django.db import models

class Couplet(models.Model):
    title = models.TextField(db_index=True, null=True)
    chapter_name = models.TextField()
    rank = models.TextField()
    text = models.TextField()

    def __unicode__(self):
        return u'{}:{}'.format(self.id, self.title or 'untitled')

class Lead(models.Model):
    letter = models.TextField()
    text = models.TextField()
    parent_couplet = models.ForeignKey(
        'Couplet', db_index=True, related_name='leads')
    result_couplet = models.ForeignKey(
        'Couplet', db_index=True, related_name='leads_to')

    def __unicode__(self):
        return u'{}:{}.{}->{}'.format(
            self.id, self.letter,
            self.parent_couplet_id, self.result_couplet_id,
            )
