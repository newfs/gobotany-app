from django.contrib import admin

from gobotany.core.models import Video
from gobotany.simplekey.models import PlainPage

class VideosInline(admin.TabularInline):
    model = PlainPage.videos.through
    extra = 0

class PlainPageAdmin(admin.ModelAdmin):
    exclude = ('videos',)
    inlines = (VideosInline,)

admin.site.register(PlainPage, PlainPageAdmin)
admin.site.register(Video)
