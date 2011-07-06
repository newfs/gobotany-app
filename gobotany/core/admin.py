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

filters_template = Template('''\
<br clear="left"><br>
{% for pile, clist in piles %}
  <h2>Pile {{ pile.name }}</h2>
  {% for character in clist %}
    <h3>{{ character.name }}</h3>
    {% for value in character.values %}
      <input type="checkbox" name="cv{{ value.id }}" value="1"
       {% if value.checked %}checked{% endif %}> {{ value.text }}<br>
    {% endfor %}
  {% endfor %}
{% endfor %}
''')

class TaxonFiltersWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        if not value:
            return u'NOTHING HERE'
        cv_ids = set( cv.id for cv in value.character_values.all() )
        pilelist = []
        for pile in value.piles.order_by('name'):
            characterdict = {}
            for cv in pile.character_values.all():
                if not cv.value_str:
                    continue
                c = cv.character
                if c.id not in characterdict:
                    characterdict[c.id] = {'name': c.name, 'values': []}
                characterdict[c.id]['values'].append({
                    'id': cv.id,
                    'text': cv.friendly_text or cv.value_str,
                    'checked': cv.id in cv_ids,
                    })
            characterlist = sorted(characterdict.values(),
                                   key=itemgetter('name'))
            pilelist.append((pile, characterlist))
        return filters_template.render(Context({
            'piles': pilelist,
            }))

class TaxonFiltersField(forms.ChoiceField):
    widget = TaxonFiltersWidget

class TaxonAdminForm(forms.ModelForm):
    filters = TaxonFiltersField()

    class Meta:
        model = models.Taxon

    def __init__(self, *args, **kw):
        super(TaxonAdminForm, self).__init__(*args, **kw)
        instance = kw.get('instance')
        if instance is not None:
            self.initial['filters'] = instance

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
