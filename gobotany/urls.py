from gobotany import views, handlers
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

    (r'^admin/', include(admin.site.urls)),
)
