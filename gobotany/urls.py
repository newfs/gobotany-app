from gobotany import views
from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    ('^$', views.default_view),
    (r'^admin/', include(admin.site.urls)),
)
