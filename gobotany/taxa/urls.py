from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from gobotany.taxa import views

urlpatterns = patterns(
    '',

    url('^family/(?P<family_slug>[a-z]+)/$',
        views.family_view, name='taxa-family'),

    # Redirections for old URLs:
    (r'^families/(?P<family_slug>[a-z]+)/$',
     redirect_to, {'url': '/family/%(family_slug)s/'}),

    )
