from django.conf.urls import url
from gobotany.dkey import views

urlpatterns = [
    url('^$', views.page, name='dkey'),
    url('^(?P<slug>[-A-Za-z0-9]+)/$', views.page, name='dkey_page'),
]
