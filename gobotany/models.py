from django.db import models


class CharacterGroup(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return u'CharacterGroup: %s id=%s' % (self.name, self.id)


class Character(models.Model):
    short_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    character_group = models.ForeignKey(CharacterGroup)

    def __unicode__(self):
        return u'Character: %s name=%s id=%s' % (self.short_name, self.name,
                                                 self.id)


class CharacterValue(models.Model):
    value = models.CharField(max_length=100)
    character = models.ForeignKey(Character)

    def __unicode__(self):
        return u'CharacterValue: character=%s value=%s id=%s' % (
            self.character.short_name,
            self.value,
            self.id)


class Pile(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    character_values = models.ManyToManyField(CharacterValue)

    def __unicode__(self):
        return u'Pile: %s id=%s' % (self.name, self.id)


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=30)
    character_values = models.ManyToManyField(CharacterValue)
    pile = models.ForeignKey(Pile)

    def __unicode__(self):
        return u'Taxon: %s pile=%s id=%s' % (self.scientific_name, self.pile,
                                             self.id)
