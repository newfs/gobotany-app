from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path
from django.views import static

from gobotany.core.admin import DistributionAdmin

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'

admin.autodiscover()

admin.site.site_title = 'Go Botany administration'
admin.site.site_header = 'Go Botany administration'

urlpatterns = []

if settings.USE_DEBUG_TOOLBAR and settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

urlpatterns += [
    path('admin/core/distribution/addset/', DistributionAdmin.add_set_view),
    path('admin/', admin.site.urls),
    path('api/', include('gobotany.api.urls')),
    path('dkey/', include('gobotany.dkey.urls')),
    path('edit/', include('gobotany.editor.urls')),
    path('plantoftheday/', include('gobotany.plantoftheday.urls')),
    path('plantshare/', include('gobotany.plantshare.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('', include('gobotany.search.urls')),
    path('', include('gobotany.site.urls')),
    path('', include('gobotany.taxa.urls')),
    path('', include('gobotany.simplekey.urls')),
]

# Serve uploaded media files as static files in development
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', static.serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
# For now, always have staticfiles turned on, even in production.

class FakeSettings():
    DEBUG = True

def fix_staticfiles():
    import django.contrib.staticfiles.views
    import django.conf.urls.static

    django.conf.urls.static.settings = FakeSettings()
    django.contrib.staticfiles.views.settings = FakeSettings()

fix_staticfiles()
urlpatterns.extend(staticfiles_urlpatterns())
