from django.conf.urls.defaults import patterns, url
from gobotany.dkey import views

urlpatterns = patterns(
    '',
    url('^$', views.page, name='dkey'),
    url('^Family-Groups/$', views.family_groups, name='dkey_family_groups'),
    url('^(?P<slug>[-A-Za-z0-9]+)/$', views.page, name='dkey_page'),
    )
