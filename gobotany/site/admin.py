from django.contrib import admin

from gobotany.site.models import SearchSuggestion

class SearchSuggestionAdmin(admin.ModelAdmin):
    search_fields = ('term',)

admin.site.register(SearchSuggestion, SearchSuggestionAdmin)
