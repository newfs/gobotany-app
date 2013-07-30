# -*- encoding: utf-8 -*-

from django import forms
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.db import models as dbmodels
from django.template import Context, Template
from django.utils.safestring import mark_safe
from gobotany.core import models

# View classes

def admin_url_from_model(model_obj):
    url = reverse('admin:{0}_{1}_change'.format(
            model_obj._meta.app_label, model_obj._meta.module_name
        ), args=(model_obj.id,))
    return url

class _Base(admin.ModelAdmin):

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(_Base, self).get_fieldsets(request, obj)

        for fieldset in fieldsets:
            options = fieldset[1]
            if options.get('description'):
                continue
            if not self.__doc__:
                continue
            prefix = '{% load gobotany_tags %}\n'
            template = Template(prefix + self.__doc__)
            options['description'] = template.render(Context({
                'obj': obj,
                'piles': models.Pile.objects,
                }))

        return fieldsets

    class Media:
        css = {'all': ('/static/admin_styles.css',)}


class TaxonSynonymInline(admin.TabularInline):
    model = models.Synonym
    extra = 1

class TaxonCommonNameInline(admin.TabularInline):
    model = models.CommonName
    extra = 1

class TaxonLookalikeInline(admin.TabularInline):
    model = models.Lookalike
    extra = 1

class TaxonAdminForm(forms.ModelForm):
    class Meta:
        model = models.Taxon
        widgets = {
            'factoid': forms.Textarea(attrs={
                    'cols': 80,
                    'rows': 10,
                    'maxlength': model._meta.get_field('factoid').max_length,
            })
        }


class TaxonAdmin(_Base):
    """

    <p>
    Each “Taxon” is variously called either a “plant” or “species”
    out on the main Go Botany web site.
    For every pile to which a Taxon is added,
    it needs to be assigned filter values
    for both multiple choice and for length based characters;
    these assignments can be made using these “Edit” links:
    </p>
    <p>
    → <a href="/species/{{ obj.genus|lower }}/{{ obj.epithet }}/"
         >View this plant's page</a> on the Go Botany site
    <br>
    {% for pile in obj.piles.all %}
    {% if not forloop.first %}<br>{% endif %}
    → <a href="/edit/cv/{{ pile.slug }}-taxa/{{ obj.slug }}/"
         >Edit this plant's character values</a> for the pile {{ pile.name }}
    {% endfor %}
    </p>

    """
    form = TaxonAdminForm
    inlines = [
        TaxonSynonymInline,
        TaxonCommonNameInline,
        TaxonLookalikeInline,
        ]
    filter_horizontal = ('piles',)
    search_fields = ('scientific_name', 'piles__name', 'piles__friendly_name')

    class Media:
        css = {'all' : ('css/admin_hide_original.css',)}

    def save_model(self, request, obj, form, change):

        this_is_an_add = obj.id is None

        # Save the object.

        super(TaxonAdmin, self).save_model(request, obj, form, change)

        # If this is a new species, we go ahead and add it to the
        # admin's partner sites.

        if this_is_an_add:
            user = request.user
            for partner in models.PartnerSite.objects.filter(users=user):
                models.PartnerSpecies(species=obj, partner=partner).save()


class GlossaryTermAdmin(_Base):
    """

    <p>
    Glossary terms affect the Go Botany site in three different ways.
    </p>
    <p>
    First, terms can appear in search results
    when the user types a search term into the text-input field
    over on the right side of the site navigation bar.
    </p>
    <p>
    Second, each glossary term
    whose <b>“Visible”</b> button is checked in the form below
    appears, along with its definition and accompanying image (if any),
    in our glossary pages, which you can visit here:
    </p>
    <p>
    <a href="/glossary/">/glossary/</a>
    </p>
    <p>
    Third, there are many pages on the site
    that highlight any glossary terms that happen to appear
    in the various paragraphs and descriptions displayed on the page.
    A glossary term is eligible for highlighting
    if its <b>“Highlight”</b> box is checked in the form below.
    When the user mouses over a glossary term,
    a popup displays the definition and any accompanying image.
    To see an example,
    mouse over the words “gametophyte” and “sporophyte”
    at the head of the Dichotomous Key:
    </p>
    <p>
    <a href="/dkey/">/dkey/</a>
    </p>

    """
    list_display = ('term', 'lay_definition', 'visible')
    search_fields = ('term', 'lay_definition')
    ordering = ('term',)
    list_filter = ('visible',)


class CharacterValuesInline(admin.TabularInline):
    model = models.CharacterValue
    extra = 0
    fields = ('value_str', 'friendly_text', 'image')
    formfield_overrides = {
        dbmodels.TextField: {'widget': forms.Textarea(attrs={'rows':4})},
        }

    def queryset(self, request):
        """Only show character values for text-type characters."""
        qs = super(CharacterValuesInline, self).queryset(request)
        qs = qs.filter(character__value_type=u'TEXT')
        return qs

class CharacterAdmin(_Base):
    """

    <p>
    A “character” is a plant characteristic
    that users can employ to filter their plant selection
    in the Simple Key and Full Key.
    Once a character has been created,
    the “edit page” for that character can be visited
    to assign each plant in the database
    can be given a  value for a given character.
    </p>
    <p>
    A character with a “Value type” of “Length” only needs
    to specify its unit of measurement,
    while a character that is “Textual” offers a set of pre-defined
    multiple choice options that should be specified
    down at the bottom of this form
    as a list of “Character values.”
    </p>

    {% if obj.pile %}
    <p>
    You can edit the value of this character
    for all of the plants in its pile here:<br>
    <a href="/edit/cv/{{ obj.pile.slug }}-characters/{{ obj.short_name }}/"
            >/edit/cv/{{ obj.pile.slug }}-characters/{{ obj.short_name }}/</a>
    </p>
    {% else %}
    <p>
    You can edit the value of this character
    for the plants in each pile of the Simple Key:
    </p>
    <p>
    {% for pile in piles.all %}
    {{ pile.name }} —
    <a href="/edit/cv/{{ pile.slug }}-characters/{{ obj.short_name }}/"
            >/edit/cv/{{ pile.slug }}-characters/{{ obj.short_name }}/</a><br>
    {% endfor %}
    </p>
    {% endif %}

    """
    list_display = ('short_name', 'character_group', 'ease_of_observability',)
    list_filter = ('character_group',)
    search_fields = ('short_name', 'name',)
    inlines = [CharacterValuesInline]

    class Media:
        css = {'all' : ('css/admin_hide_original.css',)}


class PilePlantPreviewCharactersInline(admin.TabularInline):
    model = models.Pile.plant_preview_characters.through
    extra = 0
    fields = ('partner_site', 'order', 'character')
    formfield_overrides = {
        dbmodels.IntegerField: {'widget': forms.TextInput(attrs={'size': 3})},
        }

class PileAdmin(_Base):
    """

    <p>
    Each Pile is a collection of plant species
    that is presented to the user as a grid or list
    when they reach “level 3” of the Simple Key or Full Key.
    </p>
    <p>
    The user first sees information about a Pile
    when they have chosen a Pile Group
    from the “level 1” page which starts the Simple Key and Full Key.
    The <b>Pilegroup</b> field shown below
    determines which Pile Group the user has to visit
    in order to see this Pile listed as an option
    on the Pile Group's “level 2” page.
    Next to an image gallery for the pile,
    the user will see paragraphs of information
    pulled from the large text fields defined below.
    </p>
    <p>
    If the images, text fields, and pile name
    make the user interested in this particular pile,
    then the user will select it and be taken to the “level 3” page
    that shows a grid or list of all this pile's plants.
    To add and remove plants from this pile,
    please visit the admin page for the Taxon instances that interest you
    where you can set the Piles to which each Taxa belongs.
    </p>
    <p>
    The initial filters that get displayed
    in the left toolbar of the level 3 page
    are defined by the “Plant preview characters” list
    down at the bottom of this form.
    By assigning each preview character an “order” integer,
    you can assure that the filters appear in the order you want.
    Each partner site can have its own list of preview characters.
    </p>
    {% if obj %}
    <p>
    You can visit the Simple Key page for this pile at:<br>
    <a href="/simple/{{ obj.pilegroup.slug }}/{{ obj.slug }}/"
            >/simple/{{ obj.pilegroup.slug }}/{{ obj.slug }}/</a>
    </p>
    <p>
    And the Full Key page for this pile is here:<br>
    <a href="/full/{{ obj.pilegroup.slug }}/{{ obj.slug }}/"
            >/full/{{ obj.pilegroup.slug }}/{{ obj.slug }}/</a>
    </p>
    {% endif %}

    """
    search_fields = ('name',)

    fields = ('slug', 'name', 'pilegroup',
              'friendly_title', 'friendly_name', 'video',
              'description', 'key_characteristics', 'notable_exceptions')
    inlines = [PilePlantPreviewCharactersInline]

    class Media:
        css = {'all' : ('css/admin_hide_original.css',)}


class PileGroupAdmin(_Base):
    """

    <p>
    When the user selects Simple Key or the Full Key,
    they are shown the key's “level 1” page,
    which is a list of every one of these Pile Group objects
    defined in the database.
    Each Pile Group is described by the text in the fields below.
    Once the user has selected a Pile Group,
    they are taken to that Pile Group's “level 2” page
    which lists the Piles inside of the group.
    A pile can be assigned to a groups
    either by visiting the admin page for the pile
    and changing its <b>Pilegroup</b> field,
    or by using the horizonal selection widget below.
    </p>
    {% if obj %}
    <p>
    You can visit the Simple Key page for this pile group at:<br>
    <a href="/simple/{{ obj.slug }}/"
            >/simple/{{ obj.slug }}/</a>
    </p>
    <p>
    And the Full Key page for this pile group is here:<br>
    <a href="/full/{{ obj.slug }}/"
            >/full/{{ obj.slug }}/</a>
    </p>
    {% endif %}

    """
    # prepopulated_fields = {"slug": ("slug",)} ?
    search_fields = ('name',)

    fields = ('slug', 'name',
              'friendly_title', 'friendly_name', 'video',
              'key_characteristics', 'notable_exceptions')


class FamilyAdmin(_Base):
    """

    <p>
    Each Family object represents a taxonomic genus,
    and makes a “family page” available where users
    can learn more about a particular family and its species.
    To assign a species to a family or remove it later,
    visit the species here in the admin interface
    and use its Family pull-down menu.
    </p>

    {% if obj %}
    <p>
    You can visit the Go Botany page for this family here:<br>
    <a href="{{ obj|url }}">{{ obj|url }}</a>
    </p>
    {% endif %}

    """
    search_fields = ('name', 'common_name')


class GenusAdmin(_Base):
    """

    <p>
    Each Genus object represents a taxonomic genus,
    and makes a “genus page” available where users
    can learn more about a particular genus and its species.
    To assign a species to a genus or remove it later,
    visit the species here in the admin interface
    and use its Genus pull-down menu.
    </p>

    {% if obj %}
    <p>
    You can visit the Go Botany page for this genus here:<br>
    <a href="{{ obj|url }}">{{ obj|url }}</a>
    </p>
    {% endif %}

    """
    search_fields = ('name', 'common_name')


def species_summary(obj):
    seq = list(models.PartnerSpecies.objects.filter(partner=obj)
               .select_related('species')
               .order_by('species__scientific_name'))
    total_number = len(seq)
    simple_number = len([ s for s in seq if s.simple_key ])
    return mark_safe(
        u'{} plants, of which {} are shown in the Simple Key<br>'
        u'<a href="/edit/partner/{}/plants/">Edit Plant List</b>'
        .format(total_number, simple_number, obj.id))

species_summary.short_description = 'Species'


class PartnerSiteAdmin(_Base):
    """

    <p>
    Each “partner site” entry represents an <b>allied organization</b>
    for whom we are hosting a customized copy of the Go Botany application.
    While their pages will display data
    from the same taxon and character tables that drive our own pages,
    they can be specific in choosing which <b>species</b> appear
    in their own versions of the Simple Key,
    and for each species they choose
    they can also provide a <b>blurb</b> to display
    at the top of their own site's copy of the Species Page.
    </p>

    <p>
    Using the filter below, you can assign <b>users</b> to a partner,
    in case you want to give their staff one or more Django admin accounts
    and let them log in here to edit their own species list or data.
    </p>

    """
    filter_horizontal = ('users',)
    readonly_fields = (species_summary,)


class PartnerSpeciesAdmin(_Base):
    """

    <p>
    Each "partner site" may have it's own list of species made available
    from the total set of species.  Use this form to assign a particular
    species to a partner site, choose whether the species will appear in
    that partner site's Simple Key, and edit the custom page heading and 
    "blurb" text which will appear on the species page for that partner
    site.
    </p>
    """
    search_fields = ('partner__short_name', 'species__scientific_name')
    list_display = ('partner', 'species')
    list_display_links = ('partner', 'species')
    list_filter = ('partner',)


class ContentImageAdmin(_Base):
    """

    <p>
    Content Images are stored on S3 Storage, which is scanned every
    night to check for new images. Creator names are cross-referenced
    with the Copyright Holder information pulled from the source spreadsheet.
    Content images are separately managed from user-uploaded, ScreenImages.
    </p>
    <p>
    NOTE: Uploaded images will be named based on the other fields entered,
    in the following format:<br />
    taxon-images/Family/Genus-species-image_type-photographer.jpg<br />
    Optional letters will be added to the name ensure uniqueness.
    </p>
    """
    search_fields = ('image', 'alt', 'creator')
    list_display = ('alt', 'image', 'creator')
    list_display_links = ('alt', 'image', 'creator')
    fields = ('alt', 'rank', 'image_type', 'content_type',
        'object_id', 'creator', 'copyright', 'image')
    readonly_fields = ('copyright',)

    def copyright(self, obj):
        copyright_obj = models.CopyrightHolder.objects.get(coded_name=obj.creator)
        url = admin_url_from_model(copyright_obj)
        markup = u'<a href={0}>{1}</a>'.format(
            url,
            'Copyright Info for {0}'.format(obj.creator)
        )
        return mark_safe(markup)

class CopyrightHolderAdmin(_Base):
    search_fields = ('coded_name', 'expanded_name', 'copyright')
    list_display = ('coded_name', 'expanded_name', 'copyright', 'date_record', 'image_count')
    list_display_links = ('coded_name', 'expanded_name', 'copyright', 'date_record')

    def image_count(self, obj):
        return models.ContentImage.objects.filter(creator=obj.coded_name).count()


class ConservationStatusAdmin(admin.ModelAdmin):
    list_display = ('taxon', 'variety_subspecies_hybrid', 'region', 's_rank',
        'endangerment_code', 'allow_public_posting')
    list_filter = ('region', 's_rank', 'endangerment_code',
        'allow_public_posting')


class DistributionAdmin(admin.ModelAdmin):
    list_display = ('scientific_name', 'state', 'county', 'present', 'native')
    list_editable = ('present', 'native',)
    list_filter = ('state', 'county', 'present', 'native')
    search_fields = ('scientific_name',)

class LookalikeAdmin(admin.ModelAdmin):
    list_display = ('taxon', 'lookalike_scientific_name',
        'lookalike_characteristic')

class HomePageImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'partner_site',)
    list_filter = ('partner_site',)

class DefaultFilterAdmin(admin.ModelAdmin):
    list_display = ('character', 'pile', 'order',)
    list_filter = ('pile',)

class PlantPreviewCharacterAdmin(admin.ModelAdmin):
    list_display = ('character', 'pile', 'order',)
    list_filter = ('pile',)

# Registrations

admin.site.register(models.Parameter)
admin.site.register(models.ImageType)
admin.site.register(models.CharacterGroup)
admin.site.register(models.SourceCitation)

admin.site.register(models.HomePageImage, HomePageImageAdmin)
admin.site.register(models.Lookalike, LookalikeAdmin)
admin.site.register(models.CopyrightHolder, CopyrightHolderAdmin)
admin.site.register(models.Taxon, TaxonAdmin)
admin.site.register(models.ContentImage, ContentImageAdmin)
admin.site.register(models.GlossaryTerm, GlossaryTermAdmin)
admin.site.register(models.Character, CharacterAdmin)
admin.site.register(models.Pile, PileAdmin)
admin.site.register(models.PileGroup, PileGroupAdmin)
admin.site.register(models.Family, FamilyAdmin)
admin.site.register(models.Genus, GenusAdmin)
admin.site.register(models.PartnerSite, PartnerSiteAdmin)
admin.site.register(models.PartnerSpecies, PartnerSpeciesAdmin)
admin.site.register(models.ConservationStatus, ConservationStatusAdmin)
admin.site.register(models.Distribution, DistributionAdmin)
admin.site.register(models.DefaultFilter, DefaultFilterAdmin)
admin.site.register(models.PlantPreviewCharacter, PlantPreviewCharacterAdmin)

