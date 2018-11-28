from django.contrib import admin
from django.db import models
from django.forms import ModelForm, TextInput, Textarea
from django.http import HttpResponseRedirect

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


"""Make a longer column heading name for ID so the number doesn't wrap."""
def lead_id_name(obj):
    return obj.id
lead_id_name.short_description = 'Lead ID'

class LeadAdminForm(ModelForm):
  class Meta:
    model = Lead
    widgets = {
        'letter': TextInput(),
    }
    fields = '__all__'

class LeadAdmin(GoBotanyModelAdmin):
    form = LeadAdminForm
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = (lead_id_name, 'letter', 'text', 'parent', 'page', 'goto_page',
        'goto_num', 'taxa_cache',)
    ordering = ('page__title',)
    readonly_fields = ('id', 'taxa_cache',)
    search_fields = ('id', 'letter', 'text', 'parent__letter', 'page__title',
        'goto_page__title', 'goto_num', 'taxa_cache',)

    def response_change(self, request, obj):
        # TODO: fix: using 'next' in URL bypasses 'Save and Continue Editing'
        response = super(LeadAdmin, self).response_change(request, obj)
        if 'next' in request.GET:
            return HttpResponseRedirect(request.GET['next'])
        else:
            return response


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
