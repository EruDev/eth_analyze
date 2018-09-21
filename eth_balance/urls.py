# _*_ encoding: utf-8 _*_
from django.conf.urls import url
from . import views


urlpatterns = [
    # url(r'^$', views.HomeView.as_view()),
    url(r'^names/$', views.query_names),
    url(r'^index/$', views.IndexView.as_view()),
    url(r'^exchange_rose/$', views.exchange_rose),
]