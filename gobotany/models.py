from django.db import models


class CharacterGroup(models.Model):
    name = models.CharField(max_length=50)


class Character(models.Model):
    short_name = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    character_group = models.ForeignKey(CharacterGroup)


class CharacterValue(models.Model):
    value = models.CharField(max_length=30)
    character = models.ForeignKey(Character)


class Pile(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=250)
    character_values = models.ManyToManyField(CharacterValue)


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=30)
    character_values = models.ManyToManyField(CharacterValue)
    pile = models.ForeignKey(Pile)
