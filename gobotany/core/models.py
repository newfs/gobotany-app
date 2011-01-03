from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError
from django.template.defaultfilters import slugify
from sorl.thumbnail.fields import ImageWithThumbnailsField
from tinymce import models as tinymce_models


class Parameter(models.Model):
    """An admin-configurable value."""
    #
    # Parameters that are defined so far:
    # "coverage_weight" - see igdt.py
    # "ease_of_observability_weight" - see igdt.py
    #
    name = models.CharField(max_length=100, unique=True)
    value = models.FloatField(null=False)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'Parameter %s value=%s' % (self.name, self.value)

class CharacterGroup(models.Model):
    """A group of characters that should be associated in the UI.

    Each Character uses a foreign key to designate the CharacterGroup to
    which it belongs.  Typically, a botany user interface will offer
    users the ability to narrow down the list of filters they can be
    shown by character groups, which might have names like "Leaf",
    "Stem", "Flower", and so forth.

    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s id=%s' % (self.name, self.id)


class GlossaryTerm(models.Model):
    """A term with definition and possibly images, for helping the user.

    Often, a glossary term defines a word that is found in character
    descriptions or even down in the text of character values, so that
    users of a botany UI can be provided with context-sensitive
    assistance to understanding the terminology.

    """
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
        return u'%s: %s' % (self.term, (self.lay_definition or
                                        self.question_text)[:30] + '...')


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
    ease_of_observability = models.PositiveSmallIntegerField(null=True,
        blank=True, choices=zip(range(1, 6), range(1, 6)))

    glossary_terms = models.ManyToManyField(
        GlossaryTerm,
        through='GlossaryTermForPileCharacter',
        blank=True,
        null=True)

    VALUE_CHOICES = {
        u'TEXT': u'Textual', # string
        u'LENGTH': u'Length', # length
        u'RATIO': u'Ratio', # float
        }
    UNIT_CHOICES = {
        u'mm': u'Millimeters',
        u'cm': u'Centimeters',
        u'm': u'Meters',
        }
    value_type = models.CharField(
        max_length=10, choices=VALUE_CHOICES.items())
    unit = models.CharField(
        max_length=2, null=True, blank=True, choices=UNIT_CHOICES.items())
    key_characteristics = models.TextField(blank=True)
    notable_exceptions = models.TextField(blank=True)

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
        >>> Character.objects.filter(character_values__pile=pile)
        []
        >>> pile.character_values.add(char_val)
        >>> Character.objects.filter(character_values__pile=pile)
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

    value_str = models.CharField(max_length=260, null=True, blank=True)
    value_min = models.FloatField(null=True, blank=True)
    value_max = models.FloatField(null=True, blank=True)
    value_flt = models.FloatField(null=True, blank=True)

    character = models.ForeignKey(Character, related_name='character_values')
    glossary_term = models.ForeignKey(GlossaryTerm, blank=True, null=True)
    key_characteristics = models.TextField(blank=True)
    notable_exceptions = models.TextField(blank=True)

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
        if (self.value_str is not None) and (not self.value_str.strip()):
            self.value_str = None
        # Check that we only have one of the value types,
        # XXX: We should validate this against the character value type
        if self.value_str is not None:
            if (self.value_min is not None or
                self.value_max is not None or
                self.value_flt is not None):
                raise ValidationError('You may only set '
                                      'one of the value types')
        if self.value_flt is not None:
            if (self.value_min is not None or
                self.value_max is not None):
                raise ValidationError('You may only set one '
                                      'of the value types')
        if self.value_min is not None or self.value_max is not None:
            if self.value_min is None or self.value_max is None:
                raise ValidationError('You must set both the maximum '
                                      'and minimum values')
            if self.value_min > self.value_max:
                raise ValidationError('The minimum value may not be greater '
                                      'than the maximum value')

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
    slug = models.SlugField(max_length=100, unique=True)
    friendly_name = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=2500, blank=True)
    images = generic.GenericRelation('ContentImage')
    youtube_id = models.CharField(max_length=20, blank=True)
    key_characteristics = tinymce_models.HTMLField(blank=True)
    notable_exceptions = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def __unicode__(self):
        return u'%s id=%s' % (self.name, self.id)

    def get_default_image(self):
        try:
            return self.images.get(rank=1, image_type__name='pile image')
        except ObjectDoesNotExist:
            return None

    def save(self, *args, **kw):
        """Set the slug if it isn't already set"""
        if not self.slug:
            self.slug = slugify(self.name)
        super(PileInfo, self).save(*args, **kw)


class Pile(PileInfo):
    """An informal grouping of species distinguished by common characters."""
    character_values = models.ManyToManyField(CharacterValue)
    species = models.ManyToManyField('Taxon', related_name='piles')
    pilegroup = models.ForeignKey('PileGroup', related_name='piles', null=True)
    default_filters = models.ManyToManyField(Character,
                                             through='DefaultFilter')
    plant_preview_characters = models.ManyToManyField(Character,
        through='PlantPreviewCharacter', related_name='preview_characters')
    sample_species_images = models.ManyToManyField(
        'ContentImage', related_name='sample_for_piles')


class PileGroup(PileInfo):
    """A group of Pile objects; the top level of basic-key navigation."""
    sample_species_images = models.ManyToManyField(
        'ContentImage', related_name='sample_for_pilegroups')


class GlossaryTermForPileCharacter(models.Model):
    """A binary relation associating glossary terms with characters.

    Note that this relationship is slightly complex: a particular
    character does not *simply* have a list of glossary terms associated
    with it!  Instead, the appropriate glossary terms depend on the pile
    being considered: the character "leaf shape" might be linked to
    glossary terms "diamond-shaped" and "square-shaped" for the pile
    Lycophytes (since lycophyte leaves are very primitive in shape),
    whereas the glossary terms might be "pinnate", "lobed", and so forth
    when the pile "Woody Angiosperms" is under consideration.

    """
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
    """The textual tags that identify image types in our image database.

    These type values are typically used to determine what part of a
    plant is featured in a particular image, and have values like
    "stems" and "flowers and fruits".  But some type values are not
    associated with taxon-specific images at all; a type like "pile
    image" might indicate a picture to be displayed when an entire pile
    is being shown in the UI, for example.

    """
    name = models.CharField(max_length=100,
                            verbose_name=u'image type', unique=True)

    def __unicode__(self):
        return self.name


class ContentImage(models.Model):
    """An image of a taxon, pile, or other element of botany content.

    Besides keeping up with permanent metadata, like whom should get
    credit for an image, objects of this class also hold an integer
    ``rank`` attribute which can be tweaked to select which images are
    considered the best and most representative, and should be displayed
    when screen space is limited.  Lower rank indicates a better image.
    In particular, only one "primary" image of ``rank=1`` is allowed for
    any given (piece of content, image type) combination.

    """
    image = ImageWithThumbnailsField('content image',
                                     max_length=300,  # long filenames
                                     upload_to='content_images',
                                     thumbnail={'size': (110, 110)},
                                     extra_thumbnails={'large': {
                                                              'size': (600,400),
                                                              },
                                                       },
                                     # XXX: Should we create
                                     # thumbnails on import or lazily?
                                     generate_on_save=True,
                                     )
    alt = models.CharField(max_length=300,
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


class Family(models.Model):
    """A biological family."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    common_name = models.CharField(max_length=100)
    description = models.TextField(verbose_name=u'description',
                                   blank=True)
    # We use 'example image' and 'example drawing' for the image types here
    images = generic.GenericRelation(ContentImage)

    class Meta:
        verbose_name_plural = 'families'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kw):
        """Set the slug if it isn't already set"""
        if not self.slug:
            self.slug = slugify(self.name)
        super(Family, self).save(*args, **kw)


class Genus(models.Model):
    """A biological genus."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    common_name = models.CharField(max_length=100)
    description = models.TextField(verbose_name=u'description',
                                   blank=True)
    #XXX: We don't have this data yet
    family = models.ForeignKey(Family, related_name='genera')
    # We use 'example image' and 'example drawing' for the image types here
    images = generic.GenericRelation(ContentImage)

    class Meta:
        verbose_name_plural = 'genera'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kw):
        """Set the slug if it isn't already set"""
        if not self.slug:
            self.slug = slugify(self.name)
        super(Genus, self).save(*args, **kw)


class Synonym(models.Model):
    """Other (generally previous) scientific names for species."""
    scientific_name = models.CharField(max_length=150)

    class Meta:
        ordering = ['scientific_name']

    def __unicode__(self):
        return self.scientific_name


class CommonName(models.Model):
   """A common name for a species, of which there can be more than one."""
   common_name = models.CharField(max_length=100)

   class Meta:
       ordering = ['common_name']

   def __unicode__(self):
       return self.common_name


class Lookalike(models.Model):
    """Species that can be mistaken for others."""
    lookalike_scientific_name = models.CharField(max_length=100)
    lookalike_characteristic = models.CharField(max_length=100)

    def __unicode__(self):
        return '%s (%s)' % (self.lookalike_scientific_name,
                            self.lookalike_characteristic)


class Taxon(models.Model):
    """Despite its general name, this currently represents a single species."""
    # TODO: taxa should probably have a "slug" as well, to prevent us
    # from having to create them on the fly in Javascript
    scientific_name = models.CharField(max_length=100, unique=True)
    family = models.ForeignKey(Family, related_name='taxa')
    genus = models.ForeignKey(Genus, related_name='taxa')
    character_values = models.ManyToManyField(
        CharacterValue,
        through='TaxonCharacterValue')
    taxonomic_authority = models.CharField(max_length=100)
    simple_key = models.BooleanField(default=True)
    images = generic.GenericRelation(ContentImage)
    habitat = models.CharField(max_length=300)
    factoid = models.CharField(max_length=300)
    uses = models.CharField(max_length=300)
    wetland_status_code = models.CharField(max_length=20)
    wetland_status_text = models.CharField(max_length=150)
    north_american_native = models.BooleanField(default=False)
    conservation_status_ct = models.CharField(max_length=100)
    conservation_status_me = models.CharField(max_length=100)
    conservation_status_ma = models.CharField(max_length=100)
    conservation_status_nh = models.CharField(max_length=100)
    conservation_status_ri = models.CharField(max_length=100)
    conservation_status_vt = models.CharField(max_length=100)
    distribution = models.CharField(max_length=50)
    invasive_in_states = models.CharField(max_length=50)
    sale_prohibited_in_states = models.CharField(max_length=50)
    description = models.CharField(max_length=500) # TODO: import descriptions
    synonyms = models.ManyToManyField(Synonym, related_name='taxa')
    common_names = models.ManyToManyField(CommonName, related_name='taxa')
    lookalikes = models.ManyToManyField(Lookalike, related_name='taxa')

    class Meta:
        verbose_name_plural = 'taxa'
        ordering = ['scientific_name']

    def __unicode__(self):
        return u'%s id=%s' % (self.scientific_name, self.id)

    def get_default_image(self):
        try:
            return self.images.get(rank=1, image_type__name='habit')
        except ObjectDoesNotExist:
            return None

    def get_piles(self):
        return [pile.name for pile in self.piles.all()]


class TaxonCharacterValue(models.Model):
    """Binary relation specifying the character values of a particular Taxon.

    The extra field `lit_source` is used to remember what literature was
    consulted to learn that a character value is indeed characteristic
    of a particular species.

    """
    taxon = models.ForeignKey(Taxon)
    character_value = models.ForeignKey(CharacterValue,
                                        related_name='taxon_character_values')
    lit_source = models.CharField(max_length=100,
                                  null=True, blank=True)

    class Meta:
        unique_together = ('taxon', 'character_value')
        verbose_name = 'taxon character value'
        verbose_name_plural = 'character values for taxon'
        ordering = ['taxon__scientific_name']

    def __unicode__(self):
        return u'%s: %s' % (self.taxon.scientific_name, self.character_value)


class TaxonGroup(models.Model):
    """A way to group taxa together for partner site collections."""
    name = models.CharField(max_length=100)
    taxa = models.ManyToManyField(Taxon, through='TaxonGroupEntry')

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class TaxonGroupEntry(models.Model):
    """A binary relation putting taxa in `TaxonGroup` collections."""
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
        return '%s: %s' % (self.group.name, self.taxon.scientific_name)


class DefaultFilter(models.Model):
    """A designation that a particular filter be shown by default for a pile.

    Each instance of this class dubs a particular `character` as one
    deserving a default filter, already displayed on the screen, when a
    user visits the given `pile`; the `order` lets administrators
    control which filters are placed towards the top of the page.

    """
    pile = models.ForeignKey(Pile)
    character = models.ForeignKey(Character)
    order = models.IntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('pile', 'character')

    def __unicode__(self):
        return '%s default #%d: %s' % (self.pile.name, self.order,
                                       self.character.friendly_name)


# Call this PartnerSite instead of just Site in order to avoid confusion
# with the Django "sites" framework.
class PartnerSite(models.Model):
    """An indicator of to which site--the default main site, or one of the
       partner sites--the associated record pertains.
    """
    short_name = models.CharField(max_length=30)

    class Meta:
        ordering = ['short_name']

    def __unicode__(self):
        return '%s' % self.short_name


class PlantPreviewCharacter(models.Model):
    """A designation that a character appear on the preview popup for a plant.
    """
    pile = models.ForeignKey(Pile)
    character = models.ForeignKey(Character)
    partner_site = models.ForeignKey(PartnerSite, blank=True, null=True)
    order = models.IntegerField()
    
    class Meta:
        ordering = ['order']
        unique_together = ('pile', 'character', 'partner_site')

    def __unicode__(self):
        return '%d: %s (%s)' % (self.order, self.character.friendly_name,
                                self.pile.name)
