from django.conf.urls.defaults import include, patterns

import gobotany.api.urls
import gobotany.core.urls
import gobotany.simplekey.urls

urlpatterns = patterns(
    '',
    (r'^simple/', include('gobotany.simplekey.urls')),
    )

urlpatterns += gobotany.core.urls.urlpatterns
urlpatterns += gobotany.api.urls.urlpatterns

if gobotany.settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': gobotany.settings.MEDIA_ROOT, 'show_indexes': True}),

        (r'^dojo/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': gobotany.settings.DEBUG_DOJO_ROOT, 'show_indexes': True}),
        )
