from django.conf.urls.defaults import patterns, url
from gobotany.dkey import views

urlpatterns = patterns(
    '',
    url('^(?P<couplet_slug>[-A-Za-z]+)/$', views.couplet, name='couplet'),
    url('^$', views.index, name='dkey'),
    )
