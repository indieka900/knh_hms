from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('create/', views.create_patient, name='create_patient'),
    path('search/', views.patient_search_ajax, name='patient_search_ajax'),
    path('list/', views.patient_list, name='patient_list'),
]