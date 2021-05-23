from django.contrib import admin

from gobotany.admin import GoBotanyModelAdmin
from gobotany.site.models import Document, SearchSuggestion

class SearchSuggestionAdmin(GoBotanyModelAdmin):
    search_fields = ('term',)
    
class DocumentAdmin(GoBotanyModelAdmin):
    list_display = ('title', 'upload', 'last_updated_at',)
    list_display_links = ('title',)

admin.site.register(Document, DocumentAdmin)
admin.site.register(SearchSuggestion, SearchSuggestionAdmin)
