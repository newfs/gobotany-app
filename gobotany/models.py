from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError


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

        >>> group,ignore = CharacterGroup.objects.get_or_create(
        ...     name=u'characters of the spores')
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
        >>> term = GlossaryTerm.objects.create(
        ...     term='Spore Form',
        ...     lay_definition='What form do the spores have?')
        >>> GlossaryTermForPileCharacter.objects.create(character=char,
        ...                                             pile=pile,
        ...                                             glossary_term=term)
        <...: "Spore Form" character=spore_form pile=Lycophytes>
        >>> char.glossary_terms.all()
        [<GlossaryTerm: "Spore Form" id=...>]

    Now our character has associated glossary terms.  Generally, we'll
    want to retrieve only the glossary term specific to the pile in
    which we are interested.  We can do by searching either with the
    pile object or the name of the pile:

        >>> char.glossary_terms.get(glossarytermforpilecharacter__pile=pile)
        <GlossaryTerm: "Spore Form" id=...>
        >>> char.glossary_terms.get(
        ...     glossarytermforpilecharacter__pile__name='Lycophytes')
        <GlossaryTerm: "Spore Form" id=...>
    """

    short_name = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    character_group = models.ForeignKey(CharacterGroup)
    glossary_terms = models.ManyToManyField(
        GlossaryTerm,
        through='GlossaryTermForPileCharacter',
        blank=True,
        null=True)

    VALUE_CHOICES = {
        u'TEXT': u'Textual', # string
        u'LENGTH': u'Length', # integer
        u'RATIO': u'Ratio', # float
        }
    value_type = models.CharField(max_length=10,
                                  choices=VALUE_CHOICES.items())

    def __unicode__(self):
        return u'%s name="%s" id=%s' % (self.short_name, self.name,
                                      self.id)


class CharacterValue(models.Model):
    """An object representing an allowed value for a botanic character
    within a pile. It is associated with both a character and pile.
    It also may be associated with a glossary term that provides
    clarifying information.  Let's demonstrate creating a
    CharacterValue and assigning it to a character:

        >>> group,ignore = CharacterGroup.objects.get_or_create(
        ...     name=u'characters of the tropophylls')
        >>> char = Character.objects.create(short_name='tropophyll_form',
        ...                                 name=u'Tropophyll Form',
        ...                                 character_group=group)
        >>> char_val = CharacterValue.objects.create(
        ...    value_str='short and scale-like',
        ...    character=char)
        >>> char_val
        <...: character=tropophyll_form value='short and scale-like' id=...>

    Now we can associate that character value with a Pile, which
    effectively associates the character with the Pile as well:

        >>> pile,ignore = Pile.objects.get_or_create(name='Lycophytes')
        >>> Character.objects.filter(charactervalue__pile=pile)
        []
        >>> pile.character_values.add(char_val)
        >>> Character.objects.filter(charactervalue__pile=pile)
        [<Character: tropophyll_form name="Tropophyll Form" id=...>]
        >>> CharacterValue.objects.filter(pile=pile)
        [<...: character=tropophyll_form value=u'short and scale-like' id=...>]

    We don't yet have an associated glossary term for this value.
    Let's make one:

        >>> term = GlossaryTerm.objects.create(
        ...     term='Short and Scale-like (Tropophylls)',
        ...     lay_definition='The Tropophylls look like small fish scales.')
       >>> char_val.glossary_term = term
       >>> char_val.glossary_term
       <GlossaryTerm: "Short and Scale-like (Tropophylls)" id=2>

    The display for the character values change depending on the type
    being used.

       >>> CharacterValue.objects.create(character=char, value_str='foo')
       <CharacterValue: character=tropophyll_form value='foo' id=2>
       >>> CharacterValue.objects.create(character=char, value_min=1)
       <CharacterValue: character=tropophyll_form value=u'1 - None' id=3>
       >>> CharacterValue.objects.create(character=char, value_flt=3.2)
       <CharacterValue: character=tropophyll_form value=3.2... id=4>
    """

    value_str = models.CharField(max_length=100, null=True)
    value_min = models.IntegerField(null=True)
    value_max = models.IntegerField(null=True)
    value_flt = models.FloatField(null=True)

    character = models.ForeignKey(Character)
    glossary_term = models.ForeignKey(GlossaryTerm, blank=True, null=True)

    def __unicode__(self):
        if self.value_min is not None:
            v = '%i - %s' % (self.value_min, unicode(self.value_max))
        elif self.value_flt is not None:
            v = self.value_flt
        else:
            v = self.value_str
        return u'character=%s value=%s id=%s' % (
            self.character.short_name,
            repr(v),
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
        verbose_name = 'glossary term'
        verbose_name_plural = 'glossary terms for piles'

    def __unicode__(self):
        return u'"%s" character=%s pile=%s' % (self.glossary_term.term,
                                             self.character.short_name,
                                             self.pile.name)


class ImageType(models.Model):
    name = models.CharField(max_length=100,
                            verbose_name=u'image type', unique=True)

    def __unicode__(self):
        return self.name


class ContentImage(models.Model):
    image = models.ImageField('content image',
                              upload_to='content_images')
    alt = models.CharField(max_length=100,
                           verbose_name=u'title (alt text)')
    rank = models.PositiveSmallIntegerField(
        choices=zip(range(1, 11), range(1, 11)))
    creator = models.CharField(max_length=100,
                               verbose_name=u'photographer')
    image_type = models.ForeignKey(ImageType,
                                   verbose_name='image type')
    description = models.TextField(verbose_name=u'description',
                                   blank=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def clean(self):
        """Some extra validation checks"""
        # Ensure there is only one canonical (rank 1) image per
        # image_type per content object
        if self.rank == 1:
            existing = ContentImage.objects.filter(
                rank=1,
                image_type=self.image_type,
                content_type=self.content_type_id,
                object_id=self.object_id).exclude(id=self.id)
            if existing:
                raise ValidationError('There is already a canonical (rank 1) '
                            '%s image for this item.' % self.image_type)

    def save(self, *args, **kw):
        # Run the clean method on save since it is apparently skipped
        # if the object is being created in an inline form.  This will
        # throw an ugly error, but it appears to be the only way to
        # ensure that the validation is enforced.
        self.clean()
        super(ContentImage, self).save(*args, **kw)

    def __unicode__(self):
        name = '"%s" - %s image for ' % (self.alt, self.image_type)
        if self.content_type.name == 'taxon':
            name += self.content_object.scientific_name
        else:
            name += '%s: %s' % (self.content_type.name, self.object_id)
        name += ' %s: %s' % (self.rank, self.image.name)
        return name


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=100, unique=True)
    character_values = models.ManyToManyField(
        CharacterValue,
        through='TaxonCharacterValue')
    taxonomic_authority = models.CharField(max_length=100)
    simple_key = models.BooleanField(default=True)
    pile = models.ForeignKey(Pile)
    images = generic.GenericRelation(ContentImage)

    class Meta:
        verbose_name_plural = 'taxa'

    def __unicode__(self):
        return u'%s pile=%s id=%s' % (self.scientific_name, self.pile,
                                      self.id)

    def get_default_image(self):
            try:
                return self.images.get(rank=1,
                                       image_type__name='habit')
            except ObjectDoesNotExist:
                return None


class TaxonCharacterValue(models.Model):
    taxon = models.ForeignKey(Taxon)
    character_value = models.ForeignKey(CharacterValue)
    lit_source = models.CharField(max_length=100,
                                  null=True, blank=True)

    class Meta:
        unique_together = ('taxon', 'character_value')
        verbose_name = 'taxon character value'
        verbose_name_plural = 'character values for taxa'

    def __unicode__(self):
        return u'%s %s' % (self.taxon, self.character_value)
