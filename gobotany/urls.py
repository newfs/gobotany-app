from django.conf.urls.defaults import include, patterns, url
import staticfiles.urls

import gobotany.api.urls
import gobotany.core.urls

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'

urlpatterns = patterns(
    '',
    (r'^api/', include('gobotany.api.urls')),
    (r'^core/', include('gobotany.core.urls')),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^', include('gobotany.simplekey.urls')),
    )

if gobotany.settings.DEBUG:
    urlpatterns += staticfiles.urls.urlpatterns

if gobotany.settings.DEBUG_DOJO:
    import os
    import gobotany
    dojo_path = os.path.abspath(os.path.join(gobotany.__path__[0],
                                             '..', '..', '..', 'dojo'))
    urlpatterns += patterns(
        '',
        (r'^dojo/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': dojo_path,
          'show_indexes': True}),
        )
