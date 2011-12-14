from django.contrib import admin

from gobotany.simplekey.models import Blurb, Video, HelpPage

class BlurbsInline(admin.StackedInline):
    model = HelpPage.blurbs.through
    extra = 0

class VideosInline(admin.TabularInline):
    model = HelpPage.videos.through
    extra = 0

class HelpPageAdmin(admin.ModelAdmin):
    exclude = ('blurbs', 'videos')
    inlines = (BlurbsInline, VideosInline,)

admin.site.register(Blurb)
admin.site.register(HelpPage, HelpPageAdmin)
admin.site.register(Video)
