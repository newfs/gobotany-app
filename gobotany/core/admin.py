from django.contrib import admin
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from autocomplete.fields import ModelChoiceField
from gobotany.core import models

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

class TaxonCharacterValueInline(admin.StackedInline):
    model = models.TaxonCharacterValue
    form = TaxonCharacterValueForm
    extra = 1

class ContentImageInline(generic.GenericStackedInline):
    model = models.ContentImage
    extra = 1

class TaxonAdminForm(forms.ModelForm):
    class Meta:
        model = models.Taxon

    def clean_character_values(self):
        """Validate that the selected character values are allowed in
        the Taxon's pile"""
        pile = self.cleaned_data['pile']
        for cv in self.cleaned_data['character_values']:
            try:
                cv.pile_set.get(id=pile.id)
            except ObjectDoesNotExist:
                raise forms.ValidationError(
                    'The value %s is not allowed for Pile %s'%(cv, pile.name))
        return self.cleaned_data['character_values']

class TaxonAdmin(GobotanyAdminBase):
    inlines = [TaxonCharacterValueInline, ContentImageInline]
    #exclude = ('character_values',)
    form = TaxonAdminForm
    # XXX: Cannot filter on a reverse relation in Django 1.2
    list_filter = ('family',)
    search_fields = ('scientific_name', 'piles__name', 'piles__friendly_name')

class PileDefaultFiltersForm(forms.ModelForm):
    class Meta:
        model = models.Pile.plant_preview_characters.through
    character = ModelChoiceField('character')

class PileDefaultFiltersInline(admin.StackedInline):
    model = models.Pile.default_filters.through
    form = PileDefaultFiltersForm
    extra = 1

class PilePlantPreviewCharactersForm(forms.ModelForm):
    class Meta:
        model = models.Pile.plant_preview_characters.through
    character = ModelChoiceField('character')

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
    inlines=[GlossaryMappingInline]
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


class TaxonGroupEntryInline(admin.TabularInline):
    model = models.TaxonGroupEntry
    extra = 5

class TaxonGroupAdmin(GobotanyAdminBase):
    search_fields = ('name', 'taxa__scientific_name')
    ordering = ('name',)
    inlines = (TaxonGroupEntryInline,)

class FamilyAdmin(GobotanyAdminBase):
    inlines = [ContentImageInline]
    search_fields = ('name', 'common_name')

class GenusAdmin(FamilyAdmin):
    list_filter = ('family',)


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
admin.site.register(models.TaxonGroup, TaxonGroupAdmin)
admin.site.register(models.TaxonCharacterValue, TaxonCharacterValueAdmin)
