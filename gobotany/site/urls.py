from django.conf.urls.defaults import patterns, url

from gobotany.site import views

urlpatterns = patterns(
    '',
    url(r'^about/', views.about_view, name='site-about'),
    url(r'^start/', views.getting_started_view, name='site-getting-started'),
    url(r'^video/', views.video_view, name='site-video'),
    url(r'^contributors/', views.contributors_view, name='site-contributors'),
    )
