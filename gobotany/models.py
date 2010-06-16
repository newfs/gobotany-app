from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


class CharacterGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return u'%s id=%s' % (self.name, self.id)


class GlossaryTerm(models.Model):
    term = models.CharField(max_length=100)
    lay_definition = models.TextField()
    formal_definition = models.TextField(blank=True)
    hint = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    # XXX: We will eventually factor this out into a distinct object
    # when we have real metadata
    image = models.ImageField(upload_to='glossary',
                              blank=True,
                              null=True)

    def __unicode__(self):
        return u'"%s" id=%s' % (self.term, self.id)


class Character(models.Model):
    """An object representing a botanic character.  A character is
    associated with a group of characters for UI purposes.  It may be
    associated with a glossary term that provides clarifying
    information.  The associated glossary term will depend on the
    Pile in which we are searching.  Let's demonstrate creating a
    Character and assigning it to a character group:

        >>> group,ignore = CharacterGroup.objects.get_or_create(name=u'characters of the spores')
        >>> char = Character.objects.create(short_name='spore_form',
        ...                                 name=u'Spore Form',
        ...                                 character_group=group)
        >>> char
        <Character: spore_form name="Spore Form" id=...>
        >>> char.character_group.name
        u'characters of the spores'
        >>> char.glossary_terms.all()
        []

    The list of associated glossary terms is empty.  Let's associate
    a definition for the 'Spore Form' character within the
    'Lycophytes' Pile:

        >>> pile,ignore = Pile.objects.get_or_create(name='Lycophytes')
        >>> term = GlossaryTerm.objects.create(term='Spore Form',
        ...                                    lay_definition='What form do the spores have?')
        >>> GlossaryTermForPileCharacter.objects.create(character=char,
        ...                                             pile=pile,
        ...                                             glossary_term=term)
        <GlossaryTermForPileCharacter: "Spore Form" character=spore_form pile=Lycophytes>
        >>> char.glossary_terms.all()
        [<GlossaryTerm: "Spore Form" id=...>]

    Now our character has associated glossary terms.  Generally, we'll
    want to retrieve only the glossary term specific to the pile in
    which we are interested.  We can do by searching either with the
    pile object or the name of the pile:

        >>> char.glossary_terms.get(glossarytermforpilecharacter__pile=pile)
        <GlossaryTerm: "Spore Form" id=...>
        >>> char.glossary_terms.get(glossarytermforpilecharacter__pile__name='Lycophytes') 
        <GlossaryTerm: "Spore Form" id=...>
    """

    short_name = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    character_group = models.ForeignKey(CharacterGroup)
    glossary_terms = models.ManyToManyField(GlossaryTerm,
                                         through='GlossaryTermForPileCharacter',
                                         blank=True,
                                         null=True)

    def __unicode__(self):
        return u'%s name="%s" id=%s' % (self.short_name, self.name,
                                      self.id)


class CharacterValue(models.Model):
    """An object representing an allowed value for a botanic character
    within a pile. It is associated with both a character and pile.
    It also may be associated with a glossary term that provides
    clarifying information.  Let's demonstrate creating a
    CharacterValue and assigning it to a character:

        >>> group,ignore = CharacterGroup.objects.get_or_create(name=u'characters of the tropophylls')
        >>> char = Character.objects.create(short_name='tropophyll_form',
        ...                                 name=u'Tropophyll Form',
        ...                                 character_group=group)
        >>> char_val = CharacterValue.objects.create(value='short and scale-like',
        ...                                          character=char)
        >>> char_val
        <CharacterValue: character=tropophyll_form value="short and scale-like" id=...>

    Now we can associate that character value with a Pile, which
    effectively associates the character with the Pile as well:

        >>> pile,ignore = Pile.objects.get_or_create(name='Lycophytes')
        >>> Character.objects.filter(charactervalue__pile=pile)
        []
        >>> pile.character_values.add(char_val)
        >>> Character.objects.filter(charactervalue__pile=pile)
        [<Character: tropophyll_form name="Tropophyll Form" id=...>]
        >>> CharacterValue.objects.filter(pile=pile)
        [<CharacterValue: character=tropophyll_form value="short and scale-like" id=...>]

    We don't yet have an associated glossary term for this value.
    Let's make one:

        >>> term = GlossaryTerm.objects.create(term='Short and Scale-like (Tropophylls)',
        ...                                    lay_definition='The Tropophylls look like small fish scales.')
       >>> char_val.glossary_term = term
       >>> char_val.glossary_term
       <GlossaryTerm: "Short and Scale-like (Tropophylls)" id=2>
    """

    value = models.CharField(max_length=100)
    character = models.ForeignKey(Character)
    glossary_term = models.ForeignKey(GlossaryTerm, blank=True, null=True)

    def __unicode__(self):
        return u'character=%s value="%s" id=%s' % (
            self.character.short_name,
            self.value,
            self.id)


class Pile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=250)
    character_values = models.ManyToManyField(CharacterValue)

    def __unicode__(self):
        return u'%s id=%s' % (self.name, self.id)


class GlossaryTermForPileCharacter(models.Model):
    character = models.ForeignKey(Character)
    pile = models.ForeignKey(Pile)
    glossary_term = models.ForeignKey(GlossaryTerm)

    class Meta:
        # Only one glossary term allowed per character/pile combination
        unique_together = ('character', 'pile')

    def __unicode__(self):
        return u'"%s" character=%s pile=%s' % (self.glossary_term.term,
                                             self.character.short_name,
                                             self.pile.name)


class ImageType(models.Model):
    name = models.CharField(max_length=30,
                            verbose_name=u'image type', unique=True)

    def __unicode__(self):
        return self.name


class ContentImage(models.Model):
    image = models.ImageField('content image',
                              upload_to='content_images')
    alt = models.CharField(max_length=100,
                           verbose_name=u'title (alt text)')
    canonical = models.BooleanField(default=False)
    image_type = models.ForeignKey(ImageType,
                                   verbose_name='image type')
    description = models.TextField(verbose_name=u'description',
                                   blank=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        name = '%s image for '%self.image_type
        if self.content_type.name == 'taxon':
            name += self.content_object.scientific_name
        else:
            name += '%s: %s'%(self.content_type.name, self.object_id)
        if self.canonical:
            name = 'Canonical ' + name
        name += ': %s'%(self.image.name)
        return name



class Taxon(models.Model):
    scientific_name = models.CharField(max_length=100, unique=True)
    character_values = models.ManyToManyField(CharacterValue)
    taxonomic_authority = models.CharField(max_length=100)
    pile = models.ForeignKey(Pile)
    images = generic.GenericRelation(ContentImage)

    def __unicode__(self):
        return u'%s pile=%s id=%s' % (self.scientific_name, self.pile,
                                      self.id)

    def get_default_image(self):
            try:
                return self.images.get(canonical=True,
                                       image_type__name='overall')
            except ObjectDoesNotExist:
                return None
