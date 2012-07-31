from django.conf.urls.defaults import patterns, url
from gobotany.dkey import views

urlpatterns = patterns(
    '',
    url('^$', views.index, name='dkey'),
    )
