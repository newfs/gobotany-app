from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin

import gobotany
from gobotany.core import views

admin.autodiscover()

urlpatterns = patterns(
    '',
    url('^$', views.default_view),

    url(r'^pile-search/(\w+)$', views.pile_search),
    url(r'^taxon-search/$', views.taxon_search),
    url(r'^glossary/?$', views.glossary_index),
    url(r'^canonical-images?$', views.canonical_images),
    url(r'^species-lists/$', views.species_lists),
    url(r'^characters/$', views.pile_characters_select),
    url(r'^characters/(?P<pile_slug>.*)/$', views.pile_characters),

    url(r'^static/(?P<path>.*)$', 'gobotany.core.views.static_serve',
        {'package': gobotany, 'relative_path': 'static', 'show_indexes': True}),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^piles-pile-groups$', views.piles_pile_groups),
    )
