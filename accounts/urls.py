from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import auth_view

urlpatterns = [
    path('login/',auth_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
