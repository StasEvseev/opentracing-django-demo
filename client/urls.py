from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.client_index, name='index'),
    url(r'^simple', views.client_simple_view, name='simple'),
]
