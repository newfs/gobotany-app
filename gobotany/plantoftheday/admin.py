from django.contrib import admin

from gobotany.plantoftheday.models import PlantOfTheDay

def exclude(modeladmin, request, queryset):
    queryset.update(include=False)
exclude.short_description = 'Exclude selected plants of the day'

def include(modeladmin, request, queryset):
    queryset.update(include=True)
include.short_description = 'Include selected plants of the day'

class PlantOfTheDayAdmin(admin.ModelAdmin):
    actions = [exclude, include]
    fields = ['scientific_name', 'partner_short_name', 'include', 'last_seen',
              'created', 'last_updated']
    list_display = ['scientific_name', 'partner_short_name', 'include',
                    'last_seen', 'created', 'last_updated']
    list_filter = ['partner_short_name', 'include', 'last_seen', 'created',
                   'last_updated']
    readonly_fields = ['scientific_name', 'partner_short_name', 'last_seen',
                       'created', 'last_updated']
    search_fields = ['scientific_name']

admin.site.register(PlantOfTheDay, PlantOfTheDayAdmin)
