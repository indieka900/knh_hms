from django.urls import path
from pharmacy import views

app_name = 'pharmacy'

urlpatterns = [
    path('', views.pharmacy_dashboard, name='pharmacy_dashboard'),
]