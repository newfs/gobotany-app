from django.db import models
from django.forms import TextInput, Textarea

from gobotany.admin import admin
from gobotany.dkey.models import Figure, Hybrid, IllustrativeSpecies, Lead, Page


class FigureAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('number', 'caption')
    search_fields = ('number', 'caption')


class HybridAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('scientific_name1', 'scientific_name2', 'text')
    search_fields = ('scientific_name1', 'scientific_name2', 'text')


class IllustrativeSpeciesAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('species_name', 'family_name', 'group_number')
    ordering = ('group_number', 'family_name', 'species_name')
    search_fields = ('group_number', 'family_name', 'species_name')


class LeadAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('page', 'letter', 'text')
    ordering = ('page__title',)
    readonly_fields = ('taxa_cache',)
    search_fields = ('page__title', 'letter', 'text')


class PageAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('title', 'rank', 'chapter')
    list_filter = ('rank',)
    ordering = ('title',)
    readonly_fields = ('breadcrumb_cache',)
    search_fields = ('title', 'chapter', 'rank')


admin.site.register(Figure, FigureAdmin)
admin.site.register(Hybrid, HybridAdmin)
admin.site.register(IllustrativeSpecies, IllustrativeSpeciesAdmin)
admin.site.register(Lead, LeadAdmin)
admin.site.register(Page, PageAdmin)
