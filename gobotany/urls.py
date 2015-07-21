from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from gobotany.core.admin import DistributionAdmin

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'

admin.autodiscover()

urlpatterns = []

if settings.USE_DEBUG_TOOLBAR and settings.DEBUG:
    import debug_toolbar
    urlpatterns.extend([
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ])

urlpatterns.extend([
    url(r'^admin/core/distribution/addset/', DistributionAdmin.add_set_view),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('gobotany.api.urls')),
    url(r'^dkey/', include('gobotany.dkey.urls')),
    url(r'^edit/', include('gobotany.editor.urls')),
    url(r'^plantoftheday/', include('gobotany.plantoftheday.urls')),
    url(r'^plantshare/', include('gobotany.plantshare.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^', include('gobotany.search.urls')),
    url(r'^', include('gobotany.site.urls')),
    url(r'^', include('gobotany.taxa.urls')),
    url(r'^', include('gobotany.simplekey.urls')),
])

# Serve uploaded media files as static files in development
if settings.DEBUG:
    urlpatterns.extend([
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    ])
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
