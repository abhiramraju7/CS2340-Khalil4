from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_panel.dashboard'),
    path('users/', views.user_list, name='admin_panel.user_list'),
    path(
        'users/<int:id>/',
        views.user_detail,
        name='admin_panel.user_detail',
    ),
    path(
        'users/<int:id>/role/',
        views.change_role,
        name='admin_panel.change_role',
    ),
    path(
        'users/<int:id>/suspend/',
        views.toggle_suspend,
        name='admin_panel.toggle_suspend',
    ),
    path('jobs/', views.job_list, name='admin_panel.job_list'),
    path(
        'jobs/<int:id>/flag/',
        views.flag_job,
        name='admin_panel.flag_job',
    ),
    path(
        'jobs/<int:id>/remove/',
        views.remove_job,
        name='admin_panel.remove_job',
    ),
    path(
        'jobs/<int:id>/restore/',
        views.restore_job,
        name='admin_panel.restore_job',
    ),
    path('audit/', views.audit_list, name='admin_panel.audit_list'),
]
