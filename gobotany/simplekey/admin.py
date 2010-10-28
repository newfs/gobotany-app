from django import forms
from django.contrib import admin

from gobotany.simplekey.models import Blurb, Page, Video, \
                                      HelpPage, GlossaryHelpPage

class PageAdmin(admin.ModelAdmin):
    filter_horizontal = ('pilegroups',)

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
admin.site.register(Page, PageAdmin)
admin.site.register(Video)