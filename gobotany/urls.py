from django.conf.urls.defaults import include, patterns

import gobotany.api.urls
import gobotany.core.urls
import gobotany.simplekey.urls

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'

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
         {'document_root': gobotany.settings.MEDIA_ROOT,
          'show_indexes': True}),
        )

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
