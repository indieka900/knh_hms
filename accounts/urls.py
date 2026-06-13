from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import auth_view, custom_logout_view, profile_view, role_permissions_view

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('admin/permissions/', role_permissions_view, name='role_permissions'),
]
