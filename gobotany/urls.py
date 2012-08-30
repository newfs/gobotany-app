from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('gobotany.api.urls')),
    url(r'^core/', include('gobotany.core.urls')),
    url(r'^dkey/', include('gobotany.dkey.urls')),
    url(r'^plantoftheday/', include('gobotany.plantoftheday.urls')),
    url(r'^ps/', include('gobotany.plantshare.urls')), # Release: plantshare/
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^', include('gobotany.site.urls')),
    url(r'^', include('gobotany.simplekey.urls')),
    )

# For now, always have staticfiles turned on, even in production.

class FakeSettings():
    DEBUG = True

def fix_staticfiles():
    import django.contrib.staticfiles.views
    import django.conf.urls.static

    django.conf.urls.static.settings = FakeSettings()
    django.contrib.staticfiles.views.settings = FakeSettings()

fix_staticfiles()
urlpatterns += staticfiles_urlpatterns()
