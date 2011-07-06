from operator import itemgetter
from django.contrib import admin
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django.template import Context, Template
from django import forms
from autocomplete.fields import ModelChoiceField
from gobotany.core import models

# Inline classes

class PartnerSpeciesInline(admin.TabularInline):
    model = models.PartnerSpecies
    extra = 1
    raw_id_fields = ('species',)

# View classes

class GobotanyAdminBase(admin.ModelAdmin):
    class Media:
        css = {
            "all": ("/static/admin_styles.css",)
            }

class TaxonCharacterValueForm(forms.ModelForm):
    class Meta:
        model = models.TaxonCharacterValue
    character_value = ModelChoiceField('character_value')
    taxon = ModelChoiceField('taxon')

class TaxonCharacterValueAdmin(GobotanyAdminBase):
    model = models.TaxonCharacterValue
    form = TaxonCharacterValueForm
    search_fields = ('taxon__scientific_name',
                     'character_value__character__short_name')

class TaxonSynonymInline(admin.StackedInline):
    model = models.Synonym
    extra = 1

class TaxonCommonNameInline(admin.StackedInline):
    model = models.CommonName
    extra = 1

class TaxonLookalikeInline(admin.StackedInline):
    model = models.Lookalike
    extra = 1

class ContentImageInline(generic.GenericStackedInline):
    model = models.ContentImage
    extra = 1

#
# The fancy widget that presents character-value choices in the Django
# Admin interface goes through several stages during the lifetime of a
# particular taxon as that taxon is presented by the Admin interface.
#
# 1. Assume a taxon whose .id is 123.  The "initial value" of the HTML
#    form field, as set by TaxonAdminForm.__init__(), will be "d123",
#    which is a special hint to the TaxonFiltersWidget that it should
#    render the character values already stored in the database for the
#    taxon whose .id is 123.  Forms never come back from the web page
#    with a "d"-value included; that only happens if the initial value
#    is being used.
#
# 2. The TaxonFiltersWidget draws a series of form elements.  A single
#    hidden element specifies the value "f123", meaning "this is a real
#    form submission, for the taxon whose id == 123".  All of the other
#    elements are checkboxes whose value is the character_value.id of
#    the character value they are representing (thus these values look
#    simply like "1", "2", and so forth).
#
# 3. When the user submits the form, something happens...?
#
# 4. Should the form need to be re-displayed because of an error or an
#    illegal value somewhere on the Taxon page, then the rendering
#    function of TaxonFiltersWidget will see the "f" in front of the
#    Taxon ID field and, instead of hitting the database to learn which
#    character values are currently set for the taxon, it will re-draw
#    the form using the selections that came in from the last version of
#    the form alongside the "f123" so that character value settings do
#    not re-set each time the user submits the form.
#
# 5. When the form is finally ready...?

filters_template = Template('''\
<br clear="left"><br>
<input type="hidden" name="{{ name }}" value="f{{ taxon_id }}">
{% for pile, clist in piles %}
  <h2>Pile {{ pile.name }}</h2>
  {% for character in clist %}
    <h3>{{ character.name }}</h3>
    {% for value in character.values %}
      <input type="checkbox" name="{{ name }}" value="{{ value.id }}"
       {% if value.checked %}checked{% endif %}> {{ value.text }}<br>
    {% endfor %}
  {% endfor %}
{% endfor %}
''')

class TaxonFiltersWidget(forms.CheckboxSelectMultiple):
    """Check box for each character value, grouped by pile."""

    def render(self, name, value, attrs=None):

        # value will either look like:
        # ['d123'] for taxons that are being newly displayed
        # ['f123', '37, '47', '782'] for taxons coming back from the form

        value.sort()  # move the taxon ID to the end of the list
        id_field = value.pop()
        taxon_id = int(id_field.lstrip('df'))
        taxon = models.Taxon.objects.get(pk=taxon_id)
        if id_field.startswith('d'):
            cv_ids = set( cv.id for cv in taxon.character_values.all() )
        else:
            cv_ids = set( int(cvid) for cvid in value )

        pilelist = []
        for pile in taxon.piles.order_by('name'):
            characterdict = {}

            # Pull pile values from the database.

            for cv in pile.character_values.all():
                if not cv.value_str:
                    continue
                c = cv.character
                if c.id not in characterdict:
                    characterdict[c.id] = {'name': c.name, 'values': []}
                if cv.friendly_text:
                    text = u'%s = %s' % (cv.value_str, cv.friendly_text)
                else:
                    text = cv.value_str
                characterdict[c.id]['values'].append({
                    'id': cv.id,
                    'text': text,
                    'checked': cv.id in cv_ids,
                    })

            # Sort characters and character values for presentation.

            characterlist = sorted(characterdict.values(),
                                   key=itemgetter('name'))
            for characterdict in characterlist:
                characterdict['values'].sort(key=itemgetter('text'))

            pilelist.append((pile, characterlist))

        return filters_template.render(Context({
            'name': name,
            'piles': pilelist,
            'taxon_id': taxon_id,
            }))

class TaxonFiltersField(forms.MultipleChoiceField):
    widget = TaxonFiltersWidget

    def valid_value(self, value):
        """Values should look like 'd123', 'f123', or '123'."""
        int(value.lstrip('df'))
        return True

class TaxonAdminForm(forms.ModelForm):
    filters = TaxonFiltersField()

    class Meta:
        model = models.Taxon

    def __init__(self, *args, **kw):
        super(TaxonAdminForm, self).__init__(*args, **kw)
        instance = kw.get('instance')
        if instance is not None:
            self.initial['filters'] = ['d%d' % instance.id]

    def clean_character_values(self):
        # Are the selected character values allowed in the Taxon's pile?
        pile = self.cleaned_data['pile']
        for cv in self.cleaned_data['character_values']:
            try:
                cv.pile_set.get(id=pile.id)
            except ObjectDoesNotExist:
                raise forms.ValidationError(
                    'The value %s is not allowed for Pile %s'%(cv, pile.name))
        return self.cleaned_data['character_values']

    def clean(self):
        data = self.cleaned_data
        #print data

        # Does the scientific name match the genus?

        genus_name = data['scientific_name'].split()[0]
        if genus_name != data['genus'].name:
            raise forms.ValidationError(
                'The genus %r in the scientific name does not match the'
                ' genus %r that you have selected for this species'
                % (genus_name, data['genus']))

        # Is the genus in the family?

        if data['genus'].family.id != data['family'].id:
            raise forms.ValidationError(
                'The genus %r belongs to the family %r but you have instead'
                ' selected the family %r for this species'
                % (data['genus'], data['genus'].family, data['family']))

        # Return!

        return self.cleaned_data

class TaxonAdmin(GobotanyAdminBase):
    inlines = [
        TaxonSynonymInline, TaxonCommonNameInline,
        TaxonLookalikeInline, ContentImageInline,
        ]
    #exclude = ('character_values',)
    filter_horizontal = ('piles',)
    form = TaxonAdminForm
    # XXX: Cannot filter on a reverse relation in Django 1.2
    list_filter = ('family',)
    #readonly_fields = ('scientific_name',)
    search_fields = ('scientific_name', 'piles__name', 'piles__friendly_name')

    # def formfield_for_manytomany(self, db_field, request, **kwargs):
    #     if db_field.name == 'character_values':
    #         pass #return TaxonCharacterValuesField()
    #     s = super(TaxonAdmin, self)
    #     return s.formfield_for_manytomany(db_field, request, **kwargs)

class PileDefaultFiltersForm(forms.ModelForm):
    class Meta:
        model = models.Pile.plant_preview_characters.through
    list_display = ('character')

class PileDefaultFiltersInline(admin.StackedInline):
    model = models.Pile.default_filters.through
    form = PileDefaultFiltersForm
    extra = 1

class PilePlantPreviewCharactersForm(forms.ModelForm):
    class Meta:
        model = models.Pile.plant_preview_characters.through
    list_display = ('character')

class PilePlantPreviewCharactersInline(admin.StackedInline):
    model = models.Pile.plant_preview_characters.through
    form = PilePlantPreviewCharactersForm
    extra = 1

class PileAdminBase(GobotanyAdminBase):
    inlines = [ContentImageInline]
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("slug",)}

class PileAdmin(PileAdminBase):
    filter_horizontal = ('species',)
    exclude = ('character_values',)
    inlines = [PileDefaultFiltersInline, ContentImageInline,
               PilePlantPreviewCharactersInline]

class GlossaryMappingInline(admin.TabularInline):
    model = models.GlossaryTermForPileCharacter
    extra = 1

class CharacterAdmin(GobotanyAdminBase):
    inlines = [GlossaryMappingInline]
    list_display = ('short_name', 'character_group', 'ease_of_observability',)
    search_fields = ('short_name', 'name',)
    list_filter = ('character_group',)


class GlossaryTermAdmin(GobotanyAdminBase):
    list_display = ('term', 'lay_definition', 'visible')
    search_fields = ('term', 'lay_definition', 'question_text')
    ordering = ('term',)
    list_filter = ('visible',)


class CharacterValuePileInline(admin.TabularInline):
    model = models.Pile.character_values.through
    extra = 0

class CharacterValueAdmin(GobotanyAdminBase):
    search_fields = ('character__short_name', 'value_str')
    ordering = ('character__short_name',)
    inlines = [CharacterValuePileInline,]


class FamilyAdmin(GobotanyAdminBase):
    inlines = [ContentImageInline]
    search_fields = ('name', 'common_name')

class GenusAdmin(FamilyAdmin):
    list_filter = ('family',)

class PartnerSiteAdmin(admin.ModelAdmin):
    inlines = (PartnerSpeciesInline,)

# Registrations

admin.site.register(models.Parameter)
admin.site.register(models.Character, CharacterAdmin)
admin.site.register(models.ContentImage)
admin.site.register(models.ImageType)
admin.site.register(models.Family, FamilyAdmin)
admin.site.register(models.Genus, GenusAdmin)
admin.site.register(models.PileGroup, PileAdminBase)
admin.site.register(models.Pile, PileAdmin)
admin.site.register(models.GlossaryTerm, GlossaryTermAdmin)
admin.site.register(models.CharacterGroup)
admin.site.register(models.CharacterValue, CharacterValueAdmin)
admin.site.register(models.Taxon, TaxonAdmin)
admin.site.register(models.TaxonCharacterValue, TaxonCharacterValueAdmin)
admin.site.register(models.PartnerSite, PartnerSiteAdmin)
