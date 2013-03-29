from collections import defaultdict, OrderedDict as odict

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError
from django.template.defaultfilters import slugify

from tinymce import models as tinymce_models

# Character short names common to all piles (no suffix)
COMMON_CHARACTERS = ['habitat', 'habitat_general', 'state_distribution']


def add_suffix_to_base_directory(image, suffix):
    """Instead of 'http://h/a/b/c' return 'http://h/a-suffix/b/c'."""
    name = image.name.replace('/', '-' + suffix + '/', 1)
    return image.storage.url(name)

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
    visible = models.BooleanField(default=True)  # whether to show in glossary
    highlight = models.BooleanField(default=True)
    # XXX: We will eventually factor this out into a distinct object
    # when we have real metadata
    image = models.ImageField(upload_to='glossary-images',
                              blank=True,
                              null=True)

    class Meta:
        verbose_name = 'glossary term'
        verbose_name_plural = 'glossary terms'
        # Don't allow duplicate definitions
        unique_together = ('term', 'lay_definition')

    def __unicode__(self):
        return u'%s: %s' % (self.term, self.lay_definition)


class Character(models.Model):
    """An object representing a botanic character.  A character is
    associated with a group of characters for UI purposes.  It may be
    associated with a glossary term that provides clarifying
    information.  The associated glossary term will depend on the
    Pile in which we are searching.  Let's demonstrate creating a
    Character and assigning it to a character group:

        >>> group,ignore = CharacterGroup.objects.get_or_create(
        ...     name=u'characters of the spores')
        >>> char = Character.objects.create(short_name='spore_form_ly',
        ...                                 name=u'Spore Form',
        ...                                 character_group=group)
        >>> char
        <Character: Spore Form (ly)>
        >>> char.character_group.name
        u'characters of the spores'

    """

    short_name = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    friendly_name = models.CharField(max_length=100)
    character_group = models.ForeignKey(CharacterGroup)
    pile = models.ForeignKey('Pile', null=True, related_name='characters')
    ease_of_observability = models.PositiveSmallIntegerField(null=True,
        blank=True, choices=zip(range(1, 6), range(1, 6)))

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
    UNIT_MM = {
        u'mm': 1.0,
        u'cm': 10.0,
        u'm': 1000.0,
        }
    value_type = models.CharField(
        max_length=10, choices=VALUE_CHOICES.items())
    unit = models.CharField(
        max_length=2, null=True, blank=True, choices=UNIT_CHOICES.items())
    question = models.TextField(blank=True)
    hint = models.TextField(blank=True)

    image = models.ImageField(upload_to='character-value-images',
                              blank=True,
                              null=True)  # the famous "DLD"

    class Meta:
        ordering = ['short_name']

    def __unicode__(self):
        if self.short_name[-3:-2] == '_':
            return u'%s (%s)' % (self.name, self.short_name[-2:])
        else:
            return u'%s' % (self.name)


class CharacterValue(models.Model):
    """An object representing an allowed value for a botanic character
    within a pile. It is associated with both a character and pile.
    It also may be associated with a glossary term that provides
    clarifying information.  Let's demonstrate creating a
    CharacterValue and assigning it to a character:

        >>> group,ignore = CharacterGroup.objects.get_or_create(
        ...     name=u'characters of the trophophylls')
        >>> char = Character.objects.create(short_name='trophophyll_form_ly',
        ...                                 name=u'Trophophyll Form',
        ...                                 character_group=group)
        >>> char_val = CharacterValue.objects.create(
        ...    value_str='short and scale-like',
        ...    character=char)
        >>> char_val
        <CharacterValue: trophophyll_form_ly: short and scale-like>

    The display for the character values change depending on the type
    being used.

       >>> CharacterValue.objects.create(character=char, value_str='foo')
       <CharacterValue: trophophyll_form_ly: foo>
       >>> CharacterValue.objects.create(character=char, value_min=1)
       <CharacterValue: trophophyll_form_ly: None>
       >>> CharacterValue.objects.create(character=char, value_flt=3.2)
       <CharacterValue: trophophyll_form_ly: 3.2>
    """

    value_str = models.CharField(max_length=260, null=True, blank=True)
    value_min = models.FloatField(null=True, blank=True)
    value_max = models.FloatField(null=True, blank=True)
    value_flt = models.FloatField(null=True, blank=True)

    character = models.ForeignKey(Character, related_name='character_values')
    friendly_text = models.TextField(blank=True)
    image = models.ImageField(upload_to='character-value-images',
                              blank=True,
                              null=True)  # the famous "DLD"

    class Meta:
        pass
        # ordering = ['character__short_name', 'value_str', 'value_flt',
        #             'value_min', 'value_max']

    @property
    def value(self):
        if self.value_flt is not None:
            return self.value_flt
        elif self.value_min is not None:
            return (self.value_min, self.value_max)
        return self.value_str

    def friendliest_text(self):
        """The official way to grab the friendly text, else the plain value."""
        f = self.friendly_text
        return f if f else self.value

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
    friendly_title = models.CharField(max_length=100, blank=True)
    images = generic.GenericRelation('ContentImage')
    video = models.ForeignKey('Video', null=True)
    key_characteristics = tinymce_models.HTMLField(blank=True)
    notable_exceptions = tinymce_models.HTMLField(blank=True)

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
    description = models.TextField(blank=True)
    species = models.ManyToManyField('Taxon', related_name='+')
    pilegroup = models.ForeignKey('PileGroup', related_name='piles', null=True)
    plant_preview_characters = models.ManyToManyField(Character,
        through='PlantPreviewCharacter', related_name='preview_characters')
    sample_species_images = models.ManyToManyField(
        'ContentImage', related_name='sample_for_piles', through='PileImage')


class PileImage(models.Model):
    """Intermediary model used to govern the many-to-many relationship
    between a Pile and its sample species images.
    """
    content_image = models.ForeignKey('ContentImage')
    pile = models.ForeignKey('Pile')
    order = models.IntegerField(null=True)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return '%s (%s: order %s)' % (self.content_image.image.name,
                                      self.pile.name, self.order)


class PileGroup(PileInfo):
    """A group of Pile objects; the top level of basic-key navigation."""
    sample_species_images = models.ManyToManyField(
        'ContentImage', related_name='sample_for_pilegroups',
        through='PileGroupImage')


class PileGroupImage(models.Model):
    """Intermediary model used to govern the many-to-many relationship
    between a PileGroup and its sample species images.
    """
    content_image = models.ForeignKey('ContentImage')
    pile_group = models.ForeignKey('PileGroup')
    order = models.IntegerField(null=True)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return '%s (%s: order %s)' % (self.content_image.image.name,
                                      self.pile_group.name, self.order)


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


def _content_image_path(instance, filename):
    ctype = instance.content_type
    dirname = 'content_images'
    if ctype is not None:
        dirname = settings.CONTENT_IMAGE_LOCATIONS.get(ctype.model,
                                                       'content_images')
        if callable(dirname):
            return dirname(instance, filename)
    return '%s/%s'%(dirname, filename)

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
    image = models.ImageField('content image',
                              max_length=300,  # long filenames
                              upload_to=_content_image_path)
    alt = models.CharField(max_length=300,
                           verbose_name=u'title (alt text)')
    rank = models.PositiveSmallIntegerField(
        choices=zip(range(1, 11), range(1, 11)))
    creator = models.CharField(max_length=100,
                               verbose_name=u'photographer')
    image_type = models.ForeignKey(ImageType,
                                   verbose_name='image type')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def thumb_small(self):
        return add_suffix_to_base_directory(self.image, '160x149')

    def thumb_large(self):
        return add_suffix_to_base_directory(self.image, '239x239')

    def image_medium(self):
        return add_suffix_to_base_directory(self.image, '1000s1000')

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
        if self.content_type.name == 'taxon' and self.content_object:
            name += self.content_object.scientific_name
        else:
            name += '%s: %s' % (self.content_type.name, self.object_id)
        name += ' %s: %s' % (self.rank, self.image.name)
        return name


class HomePageImage(models.Model):
    """An image that appears on the home page, cycled among others."""
    image = models.ImageField(upload_to='home-page-images')

    class Meta:
        ordering = ['image']  # users prefix filenames with "01_", "02_", etc

    def __unicode__(self):
        return '%d: %s' % (self.order, self.image.name)


class Family(models.Model):
    """A biological family."""
    name = models.CharField(max_length=100, unique=True)
    common_name = models.CharField(max_length=100)
    description = models.TextField(verbose_name=u'description',
                                   blank=True)
    # We use 'example image' and 'example drawing' for the image types here
    images = generic.GenericRelation(ContentImage)

    class Meta:
        verbose_name = 'family'
        verbose_name_plural = 'families'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower()

class Genus(models.Model):
    """A biological genus."""
    name = models.CharField(max_length=100, unique=True)
    common_name = models.CharField(max_length=100)
    description = models.TextField(verbose_name=u'description', blank=True)
    family = models.ForeignKey(Family, related_name='genera')
    # We use 'example image' and 'example drawing' for the image types here
    images = generic.GenericRelation(ContentImage)

    class Meta:
        verbose_name = 'genus'
        verbose_name_plural = 'genera'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower()

class Synonym(models.Model):
    """Other (generally previous) scientific names for species."""
    scientific_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=150)
    taxon = models.ForeignKey('Taxon', related_name='synonyms')

    class Meta:
        ordering = ['scientific_name']

    def __unicode__(self):
        return '%s (%s)' % (self.scientific_name, self.full_name)


class CommonName(models.Model):
    """A common name for a species, of which there can be more than one."""
    common_name = models.CharField(max_length=100)
    taxon = models.ForeignKey('Taxon', related_name='common_names')

    class Meta:
        ordering = ['common_name']

    def __unicode__(self):
        return self.common_name


class Lookalike(models.Model):
    """Species that can be mistaken for others."""
    lookalike_scientific_name = models.CharField(max_length=100)
    lookalike_characteristic = models.CharField(max_length=900)
    taxon = models.ForeignKey('Taxon', related_name='lookalikes')

    def __unicode__(self):
        return '%s (%s)' % (self.lookalike_scientific_name,
                            self.lookalike_characteristic)


class WetlandIndicator(models.Model):
    """An indicator category for the wetland status of a plant."""
    code = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=50)
    friendly_description = models.CharField(max_length=200)
    sequence = models.IntegerField()

    class Meta:
        ordering = ['sequence']

    def __unicode__(self):
        return '%s (%s)' % (self.code, self.name)


class Taxon(models.Model):
    """Despite its general name, this currently represents a single species."""

    scientific_name = models.CharField(max_length=100, unique=True)
    piles = models.ManyToManyField(
        Pile, through=Pile.species.through, related_name='+', blank=True)
    family = models.ForeignKey(Family, related_name='taxa')
    genus = models.ForeignKey(Genus, related_name='taxa')
    character_values = models.ManyToManyField(
        CharacterValue,
        through='TaxonCharacterValue')
    taxonomic_authority = models.CharField(max_length=100)
    images = generic.GenericRelation(ContentImage)
    factoid = models.CharField(max_length=1000, blank=True)
    wetland_indicator_code = models.CharField(max_length=15, blank=True,
                                              null=True)
    north_american_native = models.NullBooleanField()
    north_american_introduced = models.NullBooleanField()
    description = models.CharField(max_length=500, blank=True)
    variety_notes = models.CharField(max_length=1000, blank=True)
    # TODO: import descriptions!

    class Meta:
        verbose_name = 'taxon'
        verbose_name_plural = 'taxa'
        ordering = ['scientific_name']

    def __unicode__(self):
        return u'%s id=%s' % (self.scientific_name, self.id)

    def slug(self):
        return self.scientific_name.lower().replace(' ', '-')

    def genus_name(self):
        """Determine the genus name without incurring a database query."""
        return self.scientific_name.split(' ', 1)[0]

    @property
    def epithet(self):
        # convenience for forming URLs
        return self.scientific_name.split(' ', 1)[1].lower()

    def all_scientific_names(self):
        """Return a list of all the scientific names for this taxon,
        including the currently accepted scientific name and any synonyms.
        """
        names = [synonym.scientific_name for synonym in self.synonyms.all()]
        names.append(self.scientific_name)
        return names

    def get_conservation_statuses(self):
        mapping = defaultdict(list)
        for row in self.conservation_statuses.all():
            mapping[settings.STATE_NAMES[row.region]].append(row.label)
        return odict(sorted(mapping.iteritems()))

    def get_distribution_and_conservation_statuses(self):
        # Order the conservation statuses such that a special value, the
        # distribution (present/absent), always comes first.
        mapping = defaultdict(list)
        for row in self.conservation_statuses.all():
            key = settings.STATE_NAMES[row.region]
            if row.label in ['present', 'absent']:
                mapping[key].insert(0, row.label)
            else:
                mapping[key].append(row.label)
        return odict(sorted(mapping.iteritems()))

    def get_default_image(self):
        try:
            return self.images.get(rank=1, image_type__name='habit')
        except ObjectDoesNotExist:
            return None

    def get_habitats(self):
        return (self.character_values.filter(character__short_name='habitat')
                .order_by('value_str'))

    def get_wetland_indicator_text(self):
        return WetlandIndicator.objects.get(
            code=self.wetland_indicator_code
            ).friendly_description

    def partners(self):
        return PartnerSite.objects.filter(species=self)

    def partner_users(self):
        users = []
        for site in self.partners():
            users.extend(site.users.all())
        return users


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
        #ordering = ['taxon__scientific_name']  # This makes queries expensive!

    def __unicode__(self):
        return u'%s: %s' % (self.taxon.scientific_name, self.character_value)


class Edit(models.Model):
    """Record of the changes that botanists have made to character values.

    Note that this table has no real foreign keys, because it intends to
    track changes to objects - like botanists, characters, and character
    values - that might later disappear; but these edit rows need to
    remain in place as a permanent record.

    An imagined sample row, to show the idea:

    rbrumback / 20 Jul / characer-value / Acer rubrum / state / MA,ME,VT

    """
    author = models.TextField()
    datetime = models.DateTimeField()
    itemtype = models.TextField(db_index=True)
    coordinate1 = models.TextField()
    coordinate2 = models.TextField()
    old_value = models.TextField()


class ConservationStatus(models.Model):
    """Zero or more conservation status values per species+region."""

    CONSERVATION_LABELS = (
        ('absent', 'Absent'),
        ('endangered', 'Endangered'),
        ('extirpated', 'Extirpated'),
        ('historic', 'Historic'),
        ('invasive', 'Invasive'),
        ('present', 'Present'),
        ('prohibited', 'Prohibited'),
        ('rare', 'Rare'),
        ('special concern', 'Special concern'),
        ('threatened', 'Threatened'),
        )

    STATE_NAMES = sorted(settings.STATE_NAMES.items(), key=lambda x: x[1])

    taxon = models.ForeignKey(Taxon, related_name='conservation_statuses')
    region = models.CharField(choices=STATE_NAMES, max_length=80)
    label = models.CharField(choices=CONSERVATION_LABELS, max_length=80)

    class Meta:
        ordering = ('region', 'label')
        unique_together = ('taxon', 'region', 'label')

    def __unicode__(self):
        return u'%s: %s' % (self.region, self.label)


class DefaultFilter(models.Model):
    """A designation that a particular filter be shown by default for a pile.

    Each instance of this class dubs a particular `character` as one
    deserving a default filter, already displayed on the screen, when a
    user visits the given `pile`; the `order` lets administrators
    control which filters are placed towards the top of the page.

    The `key` value will typically be either the string `'simple'` or
    the string `'full'`.

    """
    key = models.CharField(max_length=36)
    pile = models.ForeignKey(Pile)
    order = models.IntegerField()
    character = models.ForeignKey(Character, null=True)

    class Meta:
        ordering = ['order']
        unique_together = ('key', 'pile', 'character')

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
    species = models.ManyToManyField(Taxon, through='PartnerSpecies')
    users = models.ManyToManyField(User)

    class Meta:
        ordering = ['short_name']

    def __unicode__(self):
        return '%s' % self.short_name

    def has_species(self, scientific_name):
        species = self.species.filter(scientific_name=scientific_name)
        return True if species else False

class PartnerSpecies(models.Model):
    """A binary relation putting taxa in `TaxonGroup` collections."""
    species = models.ForeignKey(Taxon)
    partner = models.ForeignKey(PartnerSite)
    # Does this species appear in the simple key for the TaxaGroup
    simple_key = models.BooleanField(default=True)
    species_page_heading = models.CharField(max_length=128, null=True,
                                            blank=True)
    species_page_blurb = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('species', 'partner')
        verbose_name = 'Partner species'
        verbose_name_plural = 'Partner species list'

    def __unicode__(self):
        return '%s: %s' % (self.partner.short_name,
                           self.species.scientific_name)


class PlantPreviewCharacter(models.Model):
    """A designation that a character appear on the preview popup for a plant.
    """
    pile = models.ForeignKey(Pile)
    character = models.ForeignKey(Character)
    partner_site = models.ForeignKey(PartnerSite, blank=True, null=True)
    order = models.IntegerField()

    class Meta:
        ordering = ('partner_site', 'order')
        unique_together = ('pile', 'character', 'partner_site')

    def __unicode__(self):
        return '%s %d: %s' % (self.pile.name, self.order,
                              self.character.friendly_name)


class Distribution(models.Model):
    """County-level distribution data for plants."""
    scientific_name = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=2)
    county = models.CharField(max_length=50)
    status = models.CharField(max_length=100)

    def __unicode__(self):
        county = ' (%s County)' % self.county if len(self.county) > 0 else ''
        return '%s: %s%s: %s' % (self.scientific_name, self.state,
                                 county, self.status)


class CopyrightHolder(models.Model):
    """A copyright holder for one or more images."""
    coded_name = models.CharField(max_length=50, unique=True)
    expanded_name = models.CharField(max_length=100)
    copyright = models.CharField(max_length=300)
    source = models.CharField(max_length=300)

    def __unicode__(self):
        unicode_string = u'%s: %s. Copyright: %s.' % (self.coded_name,
                                                      self.expanded_name,
                                                      self.copyright)
        if self.source:
            unicode_string += u' Source: %s' % self.source
        return unicode_string


class Video(models.Model):
    """Information on YouTube videos used for help."""
    title = models.CharField(max_length=100)
    youtube_id = models.CharField(max_length=20)
    # May want to fetch additional metadata from YouTube and store it.
    # Can retrieve Atom XML with a GET request, e.g.,
    # http://gdata.youtube.com/feeds/api/videos/LQ-jv8g1YVI?v=2
    # See docs: http://bit.ly/c1vHUz

    def __unicode__(self):
        return u'%s: %s' % (self.title, self.youtube_id)
