from django.conf.urls.defaults import patterns, url
from gobotany.simplekey import views

urlpatterns = patterns(
    '',
    url('^$', views.index_view),
    url('^collections/(?P<slug>[^/]*)/$', views.collection_view),
    url('^piles/(?P<name>[^/]*)/$', views.pile_view),
    url('^results/(?P<pile_name>[^/]*)/$', views.results_view),
    url('^results/(?P<pile_group_name>[^/]*)/(?P<pile_name>[^/]*)/$', views.results_view),
)