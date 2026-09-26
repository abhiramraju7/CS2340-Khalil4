from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='jobs.index'),
    path('mine/', views.my_listings, name='jobs.my_listings'),
    path('new/', views.create, name='jobs.create'),
    path('<int:job_id>/edit/', views.edit, name='jobs.edit'),
    path('<int:job_id>/applicants/', views.pipeline, name='jobs.pipeline'),
    path('applications/<int:application_id>/status/', views.update_application_status, name='jobs.application_status'),
]
