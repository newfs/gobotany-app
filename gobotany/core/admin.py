from django.contrib import admin
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from gobotany.core import models

class TaxonCharacterValueInline(admin.StackedInline):
    model = models.TaxonCharacterValue
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

class TaxonAdmin(admin.ModelAdmin):
    inlines = [TaxonCharacterValueInline, ContentImageInline]
    form = TaxonAdminForm
    # XXX: Cannot filter on a reverse relation in Django 1.2
    # list_filter = ('piles',)
    search_fields = ('scientific_name', 'piles__name', 'piles__friendly_name')

class PileAdminBase(admin.ModelAdmin):
    inlines = [ContentImageInline]
    search_fields = ('name',)

class PileAdmin(PileAdminBase):
    filter_horizontal = ('character_values', 'species',)

class GlossaryMappingInline(admin.TabularInline):
    model = models.GlossaryTermForPileCharacter
    extra = 1

class CharacterAdmin(admin.ModelAdmin):
    inlines=[GlossaryMappingInline]
    list_display = ('short_name', 'character_group',)
    search_fields = ('short_name', 'name',)
    list_filter = ('character_group',)


class GlossaryTermAdmin(admin.ModelAdmin):
    list_display = ('term', 'lay_definition', 'visible')
    search_fields = ('term', 'lay_definition', 'question_text')
    ordering = ('term',)
    list_filter = ('visible',)


class CharacterValueAdmin(admin.ModelAdmin):
    search_fields = ('character__short_name', 'value_str')
    ordering = ('character__short_name',)


class TaxonGroupEntryInline(admin.TabularInline):
    model = models.TaxonGroupEntry
    extra = 5

class TaxonGroupAdmin(admin.ModelAdmin):
    search_fields = ('name', 'taxa__scientific_name')
    ordering = ('name',)
    inlines = (TaxonGroupEntryInline,)


admin.site.register(models.Character, CharacterAdmin)
admin.site.register(models.ContentImage)
admin.site.register(models.ImageType)
admin.site.register(models.PileGroup, PileAdminBase)
admin.site.register(models.Pile, PileAdmin)
admin.site.register(models.GlossaryTerm, GlossaryTermAdmin)
admin.site.register(models.CharacterGroup)
admin.site.register(models.CharacterValue, CharacterValueAdmin)
admin.site.register(models.Taxon, TaxonAdmin)
admin.site.register(models.TaxonGroup, TaxonGroupAdmin)
