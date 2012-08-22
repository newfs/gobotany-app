from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from gobotany.site import views

urlpatterns = patterns(
    '',

    # Home page
    url(r'^$', views.home_view, name='site-home'),

    # Teaching page
    url('^teaching/$', views.teaching_view, name='site-teaching'),

    # About section
    url(r'^about/$', views.about_view, name='site-about'),
    url(r'^start/$', views.getting_started_view, name='site-getting-started'),
    url(r'^map/$', views.advanced_map_view, name='site-advanced-map'),
    url(r'^glossary/(?P<letter>[1a-z])/$', views.glossary_view,
        name='site-glossary'),
    url(r'^glossary/$', views.glossary_main_view, name='site-glossary-main'),
    url(r'^video/$', views.video_view, name='site-video'),
    url(r'^contributors/$', views.contributors_view,
        name='site-contributors'),

    # Legal notification pages
    url('^privacy/$', views.privacy_view, name='site-privacy'),
    url('^terms-of-use/$', views.terms_of_use_view, name='site-terms-of-use'),

    # Redirects for old URLs
    url('^teaching-tools/$', redirect_to, {'url': '/teaching/'}),
    url(r'^help/about/$', redirect_to, {'url': '/about/'}),
    url(r'^help/start/$', redirect_to, {'url': '/start/'}),
    url('^help/map/$', redirect_to, {'url': '/map/'}),
    url('^help/glossary/(?P<letter>[1a-z])/$', redirect_to,
        {'url': '/glossary/%(letter)s/'}),
    url('^help/glossary/$', redirect_to, {'url': '/glossary/'}),
    url('^help/video/$', redirect_to, {'url': '/video/'}),
    url('^help/contributors/$', redirect_to, {'url': '/contributors/'}),
    url('^legal/privacy-policy/$', redirect_to, {'url': '/privacy/'}),
    url('^legal/terms-of-use/$', redirect_to, {'url': '/terms/'}),
    )
