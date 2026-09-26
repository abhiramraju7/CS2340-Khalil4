from django.urls import path

from . import views


urlpatterns = [
    path('', views.inbox, name='messaging.inbox'),
    path('compose/', views.compose, name='messaging.compose'),
]
