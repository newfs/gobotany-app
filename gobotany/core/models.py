import string
from collections import defaultdict, OrderedDict as odict
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator
from django.forms import ValidationError
from django.template.defaultfilters import slugify

from tinymce import models as tinymce_models

# Character short names common to all piles (no suffix)
COMMON_CHARACTERS = ['habitat', 'habitat_general', 'state_distribution']


def add_suffix_to_base_directory(image, suffix):
    """Instead of 'http://h/a/b/c' return 'http://h/a-suffix/b/c'."""
    name = image.name.replace('/', '-' + suffix + '/', 1)
    return image.storage.url(name)


class NameManager(models.Manager):
    """Allow import by natural keys for partner sites"""
    def get_by_natural_key(self, name):
        return self.get(name=name)


class ShortNameManager(models.Manager):
    """Allow import by natural keys for partner sites"""
    def get_by_natural_key(self, short_name):
        return self.get(short_name=short_name)


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

    objects = NameManager()

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u'%s id=%s' % (self.name, self.id)

    def natural_key(self):
        return (self.name,)


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
    pile = models.ForeignKey('Pile', null=True, related_name='characters', blank=True)
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

    objects = ShortNameManager()

    class Meta:
        ordering = ['short_name']

    def __unicode__(self):
        if self.short_name[-3:-2] == '_':
            return u'%s (%s)' % (self.name, self.short_name[-2:])
        else:
            return u'%s' % (self.name)

    def natural_key(self):
        return (self.short_name,)


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

    objects = NameManager()

    def natural_key(self):
        return (self.name,)

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
    # Normally only 2 characters long, but save some space just in case
    code = models.CharField(max_length=4,
                            verbose_name=u'type code')

    objects = NameManager()

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


# Converts a numeric index (e.g. 233) to a alpha index (e.g. aac)
# See http://stackoverflow.com/questions/2063425/python-elegant-inverse-function-of-intstring-base
# and linked thread.
def _to_image_suffix(num):
    digits = string.lowercase
    base = len(digits)
    if num == 0:
        return ''
    
    result = []
    current = num - 1
    while current:
        result.append(digits[(current % base)])
        current = (current // base)
    else:
        if not result:
            result = ['a']
    
    result.reverse()
    return ''.join(result)

def _content_image_filename(instance, filename):
    """ Rename uploaded images based on other instance model information,
    so the file naming scheme remains consistent when uploaded via the admin.
    """
    sections = []
    # ContentType is assumed to be Taxon for all current ContentImages, because
    # they currently all ARE associated with Taxon.  If this changes in the
    # future this naming convention will need to be dropped or rethought.
    taxon = Taxon.objects.get(pk=instance.object_id)
    sections.extend(taxon.scientific_name.lower().split())
    sections.append(instance.image_type.code)
    sections.append(instance.creator)
    # Find any matching images to get our subscript
    base_name = '-'.join(sections)
    image_query = ContentImage.objects.filter(image__contains=base_name)
    if instance.pk:
        image_query = image_query.exclude(pk=instance.pk)
    matching_images = image_query.count()
    image_index = ''
    if matching_images > 0:
        # Handle some seriously long image lists
        image_index = _to_image_suffix(matching_images)
        sections.append(image_index)

    ext = filename[filename.rfind('.'):]
    new_filename = '{0}{1}'.format('-'.join(sections), ext)

    return new_filename

def _content_image_path(instance, filename):
    ctype = instance.content_type
    filename = _content_image_filename(instance, filename)
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
                              upload_to=_content_image_path,
                              help_text='Image will be renamed and moved based on other field information.')
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


def _partner_subdirectory_path(instance, filename):
    path_segments = []
    if instance.root_path:
        path_segments.append(instance.root_path)
    if instance.partner_site:
        path_segments.append(instance.partner_site.short_name)
    path_segments.append(filename)

    return '/'.join(path_segments)


class HomePageImage(models.Model):
    """An image that appears on the home page, cycled among others."""
    root_path = 'home-page-images'
    partner_site = models.ForeignKey('PartnerSite', related_name='home_page_images')
    image = models.ImageField(upload_to=_partner_subdirectory_path)

    class Meta:
        # users prefix filenames with "01_", "02_", etc.
        ordering = ['partner_site', 'image']

    def __unicode__(self):
        return self.image.name


class Family(models.Model):
    """A biological family."""
    name = models.CharField(max_length=100, unique=True)
    common_name = models.CharField(max_length=100)
    description = models.TextField(verbose_name=u'description',
                                   blank=True)
    # We use 'example image' and 'example drawing' for the image types here
    images = generic.GenericRelation(ContentImage)

    objects = NameManager()

    class Meta:
        verbose_name = 'family'
        verbose_name_plural = 'families'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower()

    def natural_key(self):
        return (self.name,)


class Genus(models.Model):
    """A biological genus."""
    name = models.CharField(max_length=100, unique=True)
    common_name = models.CharField(max_length=100)
    description = models.TextField(verbose_name=u'description', blank=True)
    family = models.ForeignKey(Family, related_name='genera')
    # We use 'example image' and 'example drawing' for the image types here
    images = generic.GenericRelation(ContentImage)

    objects = NameManager()

    class Meta:
        verbose_name = 'genus'
        verbose_name_plural = 'genera'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    @property
    def slug(self):
        return self.name.lower()

    def natural_key(self):
        return (self.name,)


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
    lookalike_characteristic = models.CharField(max_length=1000, blank=True)
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


class TaxonManager(models.Manager):
    def get_by_natural_key(self, scientific_name):
        return self.get(scientific_name=scientific_name)


class Taxon(models.Model):
    """Despite its general name this currently represents a single species."""
    objects = TaxonManager()

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

    def natural_key(self):
        return (self.scientific_name,)

    objects = TaxonManager()

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

    def get_state_distribution_labels(self):
        """For each state covered on the site, return a label indicating
        the presence or absence of the species, and, where applicable,
        any invasive status.
        """
        states = [key.upper() for key in settings.STATE_NAMES.keys()]
        distributions = Distribution.objects.all_records_for_plant(
            self.scientific_name).filter(state__in=states).values_list(
            'state', 'present')
        invasive_statuses = InvasiveStatus.objects.filter(
            taxon=self).values_list('region', 'invasive_in_region',
            'prohibited_from_sale')
        invasive_dict = {state: (invasive, prohibited)
            for state, invasive, prohibited in invasive_statuses}
        mapping = {settings.STATE_NAMES[state.lower()]: 'absent'
                   for state in states}
        for state, present in distributions:
            if present == True:
                state = state.lower()
                key = settings.STATE_NAMES[state]
                label = 'present'
                if state in invasive_dict.keys():
                    invasive, prohibited = invasive_dict[state]
                    if invasive:
                        label += ', invasive'
                    if prohibited:
                        label += ', prohibited'
                mapping[key] = label
        labels = odict(sorted(mapping.iteritems()))
        return labels

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

    def natural_key(self):
        return (self.scientific_name,)


class SourceCitation(models.Model):
    """A reference citation for a particular piece of literature.

    These citations are used to track the literature that was consulted to
    learn that a character value is indeed characteristic of a particular
    species.

    """
    citation_text = models.CharField(max_length=300)
    author = models.CharField(max_length=100, blank=True,
            verbose_name=u'Author or Editor')
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True,
            verbose_name=u'Publication Year', validators=[
                MaxValueValidator(datetime.now().year),
            ])
    article_title = models.CharField(max_length=100, blank=True,
            verbose_name=u'Article Title')
    publication_title = models.CharField(max_length=100, blank=True,
            verbose_name=u'Periodical or Book Title')
    publisher_name = models.CharField(max_length=100, blank=True,
            verbose_name=u'Publisher Name')
    publisher_location = models.CharField(max_length=100, blank=True,
            verbose_name=u'Publisher Location')

    class Meta:
        ordering = ['citation_text']

    def __unicode__(self):
        return u'{0}'.format(self.citation_text)


class TaxonCharacterValue(models.Model):
    """Binary relation specifying the character values of a particular Taxon.

    """
    taxon = models.ForeignKey(Taxon)
    character_value = models.ForeignKey(CharacterValue,
                                        related_name='taxon_character_values')
    literary_source = models.ForeignKey(SourceCitation,
                                        related_name='taxon_character_values',
                                        null=True)

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
    STATE_NAMES = sorted([(abbrev.upper(), name)
                         for abbrev, name in settings.STATE_NAMES.items()],
                         key=lambda x: x[1])

    taxon = models.ForeignKey(Taxon, related_name='conservation_statuses')
    variety_subspecies_hybrid = models.CharField(max_length=80, blank=True)
    region = models.CharField(choices=STATE_NAMES, max_length=80)
    s_rank = models.CharField(max_length=10, blank=True)
    endangerment_code = models.CharField(max_length=10, blank=True)
    allow_public_posting = models.BooleanField(default=True)

    class Meta:
        ordering = ('taxon', 'variety_subspecies_hybrid', 'region')
        verbose_name = 'conservation status'
        verbose_name_plural = 'conservation statuses'

    def __unicode__(self):
        return u'%s %s in %s: %s %s' % (self.taxon.scientific_name,
            self.variety_subspecies_hybrid, self.region, self.s_rank,
            self.endangerment_code)

    def region_name(self):
        """Return the human-readable name for a region."""
        return settings.STATE_NAMES[self.region.lower()]


class InvasiveStatus(models.Model):
    """A list of states that have designated a plant as being invasive or
    prohibited from being sold. Note that we store the lowercase state codes.

    """

    STATE_NAMES = sorted(settings.STATE_NAMES.items())

    taxon = models.ForeignKey(Taxon, related_name='invasive_statuses')
    region = models.CharField(choices=STATE_NAMES, max_length=80)
    invasive_in_region = models.NullBooleanField(default=None)
    prohibited_from_sale = models.NullBooleanField(default=None)

    class Meta:
        ordering = ('taxon', 'region')
        verbose_name = 'invasive status'
        verbose_name_plural = 'invasive statuses'

    def __unicode__(self):
        return u'%s in %s: %s %s' % (self.taxon.scientific_name,
            self.region, self.invasive_in_region,
            self.prohibited_from_sale)

    def region_name(self):
        """Return the human-readable name for a region."""
        return settings.STATE_NAMES[self.region.lower()]


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

    objects = ShortNameManager()

    class Meta:
        ordering = ['short_name']

    def __unicode__(self):
        return '%s' % self.short_name

    def has_species(self, scientific_name):
        species = self.species.filter(scientific_name=scientific_name)
        return True if species else False

    def natural_key(self):
        return (self.short_name,)

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


class DistributionManager(models.Manager):
    def all_records_for_plant(self, scientific_name):
        """Look up the plant and get its distribution records.

        Get two sets of records together:
        1. All the records for the exact scientific name
        2. Any additional records that start with the scientific name
           followed by a space

        This is done to safely pick up any additional records with
        subspecific epithets (ssp., var., etc.). These are included on the
        map because the maps are made for the species pages, which feature
        both the species information and any subspecific information.
        """
        return self.filter(
            Q(scientific_name=scientific_name) |
            Q(scientific_name__startswith=scientific_name + ' ')
        )


class Distribution(models.Model):
    """County- or state-level distribution data for plants."""
    scientific_name = models.CharField(max_length=100, db_index=True)

    species_name = models.CharField(max_length=60, db_index=True, default='')
    subspecific_epithet = models.CharField(max_length=60, db_index=True,
        default='')

    state = models.CharField(max_length=2, db_index=True)
    county = models.CharField(max_length=50, blank=True)
    present = models.BooleanField(default=False)
    native = models.BooleanField(default=False)

    class Meta:
        ordering = ('scientific_name', 'state', 'county')
        verbose_name = 'Distribution record'

    def __unicode__(self):
        county = ' (%s County)' % self.county if len(self.county) > 0 else ''
        status = ''
        if self.present:
            status = 'present, '
            if self.native:
                status += 'native'
            else:
                status += 'non-native'
        else:
            status = 'absent'
        return '%s: %s%s: %s' % (self.scientific_name, self.state,
                                 county, status)

    objects = DistributionManager()


class CopyrightHolder(models.Model):
    """A copyright holder for one or more images."""
    coded_name = models.CharField(max_length=50, unique=True)
    expanded_name = models.CharField(max_length=100)
    copyright = models.CharField(max_length=300)
    source = models.CharField(max_length=300)
    contact_info = models.CharField(max_length=300)

    # Additional fields, imported as text.  These may need to change later.
    primary_bds = models.CharField(max_length=300)
    date_record = models.CharField(max_length=300)
    last_name = models.CharField(max_length=300)
    permission_source = models.CharField(max_length=300)
    permission_level = models.CharField(max_length=300)
    permission_location = models.CharField(max_length=300)
    notes = models.CharField(max_length=1000)

    def __unicode__(self):
        unicode_string = u'%s: %s. Copyright: %s.' % (self.coded_name,
                                                      self.expanded_name,
                                                      self.copyright)
        if self.contact_info:
            unicode_string += u' Contact Info: %s' % self.contact_info
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
