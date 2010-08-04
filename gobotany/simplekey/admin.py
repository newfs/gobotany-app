from django.contrib import admin
from gobotany.simplekey.models import Blurb, Page

class PageAdmin(admin.ModelAdmin):
    filter_horizontal = ('pilegroups',)

admin.site.register(Blurb)
admin.site.register(Page, PageAdmin)
