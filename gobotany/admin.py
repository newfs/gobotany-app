from django.contrib import admin

class GoBotanyModelAdmin(admin.ModelAdmin):
    """Subclass ModelAdmin in order to add custom CSS and JS globally."""

    class Media:
        css = {
            'all': ('/static/admin/admin_gb.css',)
        }
        js = ('/static/admin/admin_gb.js',)