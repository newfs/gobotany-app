from django.db import models


class CharacterGroup(models.Model):
    name = models.CharField(max_length=100)


class Character(models.Model):
    short_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    character_group = models.ForeignKey(CharacterGroup)


class CharacterValue(models.Model):
    value = models.CharField(max_length=100)
    character = models.ForeignKey(Character)


class Pile(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    character_values = models.ManyToManyField(CharacterValue)


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=30)
    character_values = models.ManyToManyField(CharacterValue)
    pile = models.ForeignKey(Pile)
