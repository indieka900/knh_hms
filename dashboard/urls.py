from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('home/', views.dashboard_view, name='home'),  # Add home alias
    path('system-reports/', views.system_reports_view, name='system_reports'),
    path('audit-logs/', views.audit_logs_view, name='audit_logs'),
    path('user-management/', views.user_management_view, name='user_management'),
    path('system-settings/', views.system_settings_view, name='settings'),
]