from django.conf.urls.defaults import patterns, url
from gobotany.simplekey import views

urlpatterns = patterns(
    '',
    url('^$', views.index_view),
    url('^(?P<number>[0-9]+)/$', views.page_view),
    url('^(?P<pilegroup_slug>[^/]*)/$', views.pilegroup_view),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$', views.results_view),
)
