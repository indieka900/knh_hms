from django.urls import path
from accounts.views import (
    # register,
    login_view,
)

app_name = 'accounts'

urlpatterns = [
    # path('register/', register, name='register'),
    path('login/', login_view, name='login'),
]