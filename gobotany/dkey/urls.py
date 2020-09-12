from django.urls import path

from gobotany.dkey import views

urlpatterns = [
    path('', views.page, name='dkey'),
    path('<slug:slug>/', views.page, name='dkey_page'),
]