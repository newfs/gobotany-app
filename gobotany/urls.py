from gobotany import views, handlers
import gobotany
from piston.resource import Resource
from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    ('^$', views.default_view),

    (r'^taxon/(?P<scientific_name>[^/]+)/$',
     Resource(handler=handlers.TaxonHandler)),
    (r'^taxon/$',
     Resource(handler=handlers.TaxonQueryHandler)),
    (r'^taxon-count/$',
     Resource(handler=handlers.TaxonCountHandler)),

    (r'^pile-search/(\w+)$', views.pile_search),
    (r'^taxon-search/$', views.taxon_search),

    (r'^static/(?P<path>.*)$', 'gobotany.views.static_serve',
     {'package': gobotany, 'relative_path': 'static', 'show_indexes': True}),

    (r'^admin/', include(admin.site.urls)),
)
