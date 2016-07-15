from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea

from gobotany.admin import GoBotanyModelAdmin
from gobotany.dkey.models import Figure, Hybrid, IllustrativeSpecies, Lead, Page


class FigureAdmin(GoBotanyModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('number', 'caption')
    search_fields = ('number', 'caption')


class HybridAdmin(GoBotanyModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('scientific_name1', 'scientific_name2', 'text')
    search_fields = ('scientific_name1', 'scientific_name2', 'text')


class IllustrativeSpeciesAdmin(GoBotanyModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('species_name', 'family_name', 'group_number')
    ordering = ('group_number', 'family_name', 'species_name')
    search_fields = ('group_number', 'family_name', 'species_name')


class LeadAdmin(GoBotanyModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = ('page', 'letter', 'text')
    ordering = ('page__title',)
    readonly_fields = ('taxa_cache',)
    search_fields = ('page__title', 'letter', 'text')


class PageAdmin(GoBotanyModelAdmin):
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
