from django.contrib import admin
from django.db import models
from django.forms import ChoiceField, ModelForm, Textarea, TextInput
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
    list_display = ('scientific_name1', 'number1', 'scientific_name2',
        'number2', 'text')
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

class LeadAdmin(GoBotanyModelAdmin):
    raw_id_fields = ('page', 'parent', 'goto_page')
    fields = ('id', 'letter', 'text', 'goto_page', 'goto_num', 'page',
        'parent', 'taxa_cache',)
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80}) },
    }
    list_display = (lead_id_name, 'letter', 'text', 'parent', 'page',
        'goto_page', 'goto_num',)
    list_select_related = ('page', 'parent', 'goto_page',)
    readonly_fields = ('id', 'page', 'parent', 'taxa_cache',)
    search_fields = ('id', 'letter', 'text', 'parent__letter', 'page__title',
        'goto_page__title', 'goto_num',)
    show_full_result_count = False

    # Use a regular small text input field for the Letter field.
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'letter':
            kwargs['widget'] = TextInput
        return super(LeadAdmin, self).formfield_for_dbfield(db_field,**kwargs)

    def response_change(self, request, obj):
        # If the response has a 'next' parameter, go to that page
        # after saving. This is for being able to return to the D. Key Editor
        # upon changing and saving a Lead.
        response = super(LeadAdmin, self).response_change(request, obj)
        save_and_continue_pressed = '_continue' in request.POST
        if 'next' in request.GET:
            if save_and_continue_pressed:
                # Add the 'next' parameter to the response URL so that
                # when one eventually presses Save, it will still go back
                # to the D. Key Editor.
                return HttpResponseRedirect(
                    response.url + '?next=' + request.GET['next'])
            else:
                # Redirect to the 'next' parameter URL, which will be to
                # the D. Key Editor.
                return HttpResponseRedirect(request.GET['next'])
        else:
            return response


class PageAdmin(GoBotanyModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 80}) },
    }
    list_display = ('title', 'rank', 'chapter')
    list_filter = ('rank',)
    ordering = ('title',)
    readonly_fields = ('breadcrumb_cache',)
    search_fields = ('title', 'chapter', 'rank')

    def get_form(self, request, obj=None, **kwargs):
        form = super(PageAdmin, self).get_form(request, obj, **kwargs)
        # Make the 'Text' text field bigger for easier editing.
        form.base_fields['text'].widget.attrs['style'] = \
            'height: 24rem; width: 48rem'
        return form


admin.site.register(Figure, FigureAdmin)
admin.site.register(Hybrid, HybridAdmin)
admin.site.register(IllustrativeSpecies, IllustrativeSpeciesAdmin)
admin.site.register(Lead, LeadAdmin)
admin.site.register(Page, PageAdmin)
