from django.contrib import admin

site = admin.site   # Pass along so just this module can be used in most cases

class ModelAdmin(admin.ModelAdmin):
    """Subclass ModelAdmin in order to add custom CSS and JS globally."""

    class Media:
        css = {
            'all': ('/static/admin/admin_gb.css',)
        }
        js = ('/static/admin/admin_gb.js',)
