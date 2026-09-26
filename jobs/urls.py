from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='jobs.index'),
    path('<int:job_id>/applicants/', views.pipeline, name='jobs.pipeline'),
    path('applications/<int:application_id>/status/', views.update_application_status, name='jobs.application_status'),
]
