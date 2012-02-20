from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.conf.urls.static import static
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
    url(r'^plantoftheday/', include('gobotany.plantoftheday.urls')),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^', include('gobotany.simplekey.urls')),
    )

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
