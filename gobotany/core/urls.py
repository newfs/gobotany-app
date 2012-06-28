from django.conf.urls.defaults import patterns, url

from gobotany.core import views

urlpatterns = patterns(
    '',
    url('^$', views.default_view),

    url(r'^best-characters/$', views.pile_characters_select),
    url(r'^best-characters/(?P<pile_slug>.*)/$', views.pile_characters),
    )
