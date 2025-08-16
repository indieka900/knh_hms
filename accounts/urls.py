from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import auth_view, custom_logout_view, profile_view, profile_edit_view, settings_view

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('settings/', settings_view, name='settings'),
]
