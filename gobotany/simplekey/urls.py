from django.conf.urls.defaults import patterns, url
from gobotany.simplekey import views

urlpatterns = patterns(
    '',
    url('^$', views.index_view),
    url('^collections/(?P<slug>[^/]*)/', views.collection_view),
    )
