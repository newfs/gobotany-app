from django.conf.urls.defaults import patterns, url
from gobotany.dkey import views

urlpatterns = patterns(
    '',
    url('^$', views.page, name='dkey'),
    url('^(?P<slug>[-A-Za-z0-9]+)/$', views.page, name='dkey_page'),
    )
