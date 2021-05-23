from django.contrib import admin

from gobotany.admin import GoBotanyModelAdmin
from gobotany.site.models import Document, SearchSuggestion

class SearchSuggestionAdmin(GoBotanyModelAdmin):
    search_fields = ('term',)
    
class DocumentAdmin(GoBotanyModelAdmin):
    list_display = ('id', 'upload', 'added_at',)

admin.site.register(Document, DocumentAdmin)
admin.site.register(SearchSuggestion, SearchSuggestionAdmin)
