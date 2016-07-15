from django.contrib import admin

from gobotany.admin import GoBotanyModelAdmin
from gobotany.site.models import SearchSuggestion

class SearchSuggestionAdmin(GoBotanyModelAdmin):
    search_fields = ('term',)

admin.site.register(SearchSuggestion, SearchSuggestionAdmin)
