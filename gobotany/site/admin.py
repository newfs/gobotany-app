from django.contrib import admin

from gobotany.admin import GoBotanyModelAdmin
from gobotany.site.models import (Document, Highlight, SearchSuggestion,
    Update)

class DocumentAdmin(GoBotanyModelAdmin):
    list_display = ('title', 'upload', 'last_updated_at',)
    list_display_links = ('title',)

class HighlightAdmin(GoBotanyModelAdmin):
    list_display = ('id', 'note', 'active',)

class SearchSuggestionAdmin(GoBotanyModelAdmin):
    search_fields = ('term',)

class UpdateAdmin(GoBotanyModelAdmin):
    list_display = ('date', 'description',)
    fields = ('date', 'description',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(UpdateAdmin, self).get_form(request, obj, **kwargs)
        # Make the 'Description' text field bigger for easier editing.
        form.base_fields['description'].widget.attrs['style'] = \
            'height: 24rem; width: 48rem'
        return form


admin.site.register(Document, DocumentAdmin)
admin.site.register(Highlight, HighlightAdmin)
admin.site.register(SearchSuggestion, SearchSuggestionAdmin)
admin.site.register(Update, UpdateAdmin)