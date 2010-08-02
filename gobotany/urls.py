from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin

import gobotany
import gobotany.api.urls
from gobotany import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url('^$', views.default_view),

    url(r'^pile-search/(\w+)$', views.pile_search),
    url(r'^taxon-search/$', views.taxon_search),
    url(r'^glossary/?$', views.glossary_index),
    url(r'^canonical-images?$', views.canonical_images),
    url(r'^species-lists/$', views.species_lists),

    url(r'^static/(?P<path>.*)$', 'gobotany.views.static_serve',
        {'package': gobotany, 'relative_path': 'static', 'show_indexes': True}),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^piles-pile-groups$', views.piles_pile_groups),

    # django-haystack
    url(r'^search/', include('haystack.urls')),
    )

urlpatterns += gobotany.api.urls.urlpatterns

if gobotany.settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': gobotany.settings.MEDIA_ROOT, 'show_indexes': True}),

        (r'^dojo/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': gobotany.settings.DEBUG_DOJO_ROOT, 'show_indexes': True}),
        )
