from django.db import models


class CharacterGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return u'CharacterGroup: %s id=%s' % (self.name, self.id)


class GlossaryTerm(models.Model):
    term = models.CharField(max_length=100)
    lay_definition = models.TextField()
    formal_definition = models.TextField(blank=True)
    hint = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    # XXX: images


class Character(models.Model):
    short_name = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    character_group = models.ForeignKey(CharacterGroup)
    glossary_terms = models.ManyToManyField(GlossaryTerm,
                                         through='GlossaryTermForPileCharacter',
                                         blank=True,
                                         null=True)

    def __unicode__(self):
        return u'Character: %s name=%s id=%s' % (self.short_name, self.name,
                                                 self.id)


class CharacterValue(models.Model):
    value = models.CharField(max_length=100)
    character = models.ForeignKey(Character)
    glossary_term = models.ForeignKey(GlossaryTerm, blank=True, null=True)

    def __unicode__(self):
        return u'CharacterValue: character=%s value=%s id=%s' % (
            self.character.short_name,
            self.value,
            self.id)


class Pile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=250)
    character_values = models.ManyToManyField(CharacterValue)

    def __unicode__(self):
        return u'Pile: %s id=%s' % (self.name, self.id)


class GlossaryTermForPileCharacter(models.Model):
    character = models.ForeignKey(Character)
    pile = models.ForeignKey(Pile)
    glossary_term = models.ForeignKey(GlossaryTerm)


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=100, unique=True)
    character_values = models.ManyToManyField(CharacterValue,
                                              through='TaxonToCharacterValue')
    taxonomic_authority = models.CharField(max_length=100)
    pile = models.ForeignKey(Pile)

    def __unicode__(self):
        return u'Taxon: %s pile=%s id=%s' % (self.scientific_name, self.pile,
                                             self.id)


class TaxonToCharacterValue(models.Model):
    taxon = models.ForeignKey(Taxon)
    character_value = models.ForeignKey(CharacterValue)

    def __unicode__(self):
        return u'TaxonToCharacterValue: taxon=%s character_value=%s id=%s' % \
               (self.taxon, self.character_value, self.id)
