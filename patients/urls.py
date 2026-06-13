from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('create/', views.create_patient, name='create_patient'),
    path('search/', views.patient_search_ajax, name='patient_search_ajax'),
]