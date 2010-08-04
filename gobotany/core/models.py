from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError


class CharacterGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s id=%s' % (self.name, self.id)


class GlossaryTerm(models.Model):
    term = models.CharField(max_length=100)
    lay_definition = models.TextField(blank=True)
    question_text = models.TextField(blank=True)
    hint = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    # XXX: We will eventually factor this out into a distinct object
    # when we have real metadata
    image = models.ImageField(upload_to='glossary',
                              blank=True,
                              null=True)
    class Meta:
        ordering = ['term', 'lay_definition']
        # Don't allow duplicate definitions
        unique_together = ('term', 'lay_definition', 'question_text')

    def __unicode__(self):
        return u'%s: %s' % (self.term, (self.lay_definition or self.question_text)[:30] + '...')


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
        [<GlossaryTerm: Spore Form:...>]

    Now our character has associated glossary terms.  Generally, we'll
    want to retrieve only the glossary term specific to the pile in
    which we are interested.  We can do by searching either with the
    pile object or the name of the pile:

        >>> char.glossary_terms.get(glossarytermforpilecharacter__pile=pile)
        <GlossaryTerm: Spore Form:...>
        >>> char.glossary_terms.get(
        ...     glossarytermforpilecharacter__pile__name='Lycophytes')
        <GlossaryTerm: Spore Form:...>
    """

    short_name = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    friendly_name = models.CharField(max_length=100)
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

    class Meta:
        ordering = ['short_name']

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
        <CharacterValue: tropophyll_form: short and scale-like>

    Now we can associate that character value with a Pile, which
    effectively associates the character with the Pile as well:

        >>> pile,ignore = Pile.objects.get_or_create(name='Lycophytes')
        >>> Character.objects.filter(charactervalue__pile=pile)
        []
        >>> pile.character_values.add(char_val)
        >>> Character.objects.filter(charactervalue__pile=pile)
        [<Character: tropophyll_form name="Tropophyll Form" id=...>]
        >>> CharacterValue.objects.filter(pile=pile)
        [<CharacterValue: tropophyll_form: short and scale-like>]

    We don't yet have an associated glossary term for this value.
    Let's make one:

        >>> term = GlossaryTerm.objects.create(
        ...     term='Short and Scale-like (Tropophylls)',
        ...     lay_definition='The Tropophylls look like small fish scales.')
       >>> char_val.glossary_term = term
       >>> char_val.glossary_term
       <GlossaryTerm: Short and Scale-like (Tropophylls): ...>

    The display for the character values change depending on the type
    being used.

       >>> CharacterValue.objects.create(character=char, value_str='foo')
       <CharacterValue: tropophyll_form: foo>
       >>> CharacterValue.objects.create(character=char, value_min=1)
       <CharacterValue: tropophyll_form: None>
       >>> CharacterValue.objects.create(character=char, value_flt=3.2)
       <CharacterValue: tropophyll_form: 3.2>
    """

    value_str = models.CharField(max_length=100, null=True, blank=True)
    value_min = models.IntegerField(null=True, blank=True)
    value_max = models.IntegerField(null=True, blank=True)
    value_flt = models.FloatField(null=True, blank=True)

    character = models.ForeignKey(Character)
    glossary_term = models.OneToOneField(GlossaryTerm, blank=True, null=True)

    class Meta:
        ordering = ['character__short_name', 'value_str', 'value_flt',
                    'value_min', 'value_max']

    @property
    def value(self):
        if self.value_flt is not None:
            return self.value_flt
        elif self.value_min is not None:
            return (self.value_min, self.value_max)
        return self.value_str

    def clean(self):
        """Make sure one and only one value type is set"""
        # no empty strings allowed
        if not self.value_str.strip(): self.value_str = None
        # Check that we only have one of the value types,
        # XXX: We should validate this against the character value type
        if self.value_str is not None:
            if (self.value_min is not None or
                self.value_max is not None or
                self.value_flt is not None):
                raise ValidationError('You may only set one of the value types')
        if self.value_flt is not None:
            if (self.value_min is not None or
                self.value_max is not None or
                self.value_str is not None):
                raise ValidationError('You may only set one of the value types')
        if self.value_min is not None or self.value_max is not None:
            if (self.value_flt is not None or
                self.value_str is not None):
                raise ValidationError('You may only set one of the value types')
            if self.value_min is None or self.value_max is None:
                raise ValidationError('You must set both the maximum and minimum values')
            if self.value_min > self.value_max:
                raise ValidationError('The minimum value may not be greater than the maximum value')

    def __unicode__(self):
        if self.value_min is not None and self.value_max is not None:
            v = u'%i - %i' % (self.value_min, self.value_max)
        elif self.value_flt is not None:
            v = unicode(self.value_flt)
        else:
            v = self.value_str
        return u'%s: %s' % (
            self.character.short_name, v)


class PileInfo(models.Model):
    """Common fields shared by Pile-like objects."""
    name = models.CharField(max_length=100, unique=True)
    friendly_name = models.CharField(max_length=100, unique=True, null=True)
    description = models.CharField(max_length=2500)
    images = generic.GenericRelation('ContentImage')
    youtube_id = models.CharField(max_length=20, blank=True)
    key_characteristics = models.TextField(blank=True)
    notable_exceptions = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def __unicode__(self):
        return u'%s id=%s' % (self.name, self.id)

    def get_default_image(self):
            try:
                return self.images.get(rank=1,
                                       image_type__name='pile image')
            except ObjectDoesNotExist:
                return None


class Pile(PileInfo):
    """An informal grouping of species distinguished by common characters."""
    character_values = models.ManyToManyField(CharacterValue)
    species = models.ManyToManyField('Taxon', related_name='piles')
    pilegroup = models.ForeignKey('PileGroup', related_name='piles', null=True)


class PileGroup(PileInfo):
    """A group of Pile objects; the top level of basic-key navigation."""
    #piles = models.ManyToManyField(Pile)


class GlossaryTermForPileCharacter(models.Model):
    character = models.ForeignKey(Character)
    pile = models.ForeignKey(Pile)
    glossary_term = models.ForeignKey(GlossaryTerm)

    class Meta:
        # Only one glossary term allowed per character/pile combination
        unique_together = ('character', 'pile')
        verbose_name = 'character glossary term'
        verbose_name_plural = 'glossary terms for characters'

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
    images = generic.GenericRelation(ContentImage)

    class Meta:
        verbose_name_plural = 'taxa'
        ordering = ['scientific_name']

    def __unicode__(self):
        return u'%s id=%s' % (self.scientific_name, self.id)

    def get_default_image(self):
            try:
                return self.images.get(rank=1,
                                       image_type__name='habit')
            except ObjectDoesNotExist:
                return None

    def get_piles(self):
            try:
                return [pile.name for pile in self.piles.all()]
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
        verbose_name_plural = 'character values for taxon'

    def __unicode__(self):
        return u'%s'%self.character_value


class TaxonGroup(models.Model):
    name = models.CharField(max_length=100)
    taxa = models.ManyToManyField(Taxon,
                                  through='TaxonGroupEntry')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class TaxonGroupEntry(models.Model):
    taxon = models.ForeignKey(Taxon)
    group = models.ForeignKey(TaxonGroup)
    # Does this species appear in the simple key for the TaxaGroup
    simple_key = models.BooleanField(default=True)

    class Meta:
        # A group can reference a taxon only once
        unique_together = ('taxon', 'group')
        ordering = ['group__name', 'taxon__scientific_name']
        verbose_name_plural = 'taxon group entries'


    def __unicode__(self):
        return '%s: %s'%(self.group.name, self.taxon.scientific_name)


class DefaultFilter(models.Model):
    pile = models.ForeignKey(Pile)
    character = models.ForeignKey(Character)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return '%d: %s (%s)' % (self.order, self.character.friendly_name,
                                self.pile.name)
