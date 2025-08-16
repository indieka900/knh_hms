from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('list/', views.patient_list, name='patient_list'),
    path('create/', views.create_patient, name='create_patient'),
    path('search/', views.patient_search_ajax, name='patient_search_ajax'),
    path('detail/<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('edit/<str:patient_id>/', views.patient_edit, name='patient_edit'),
    path('delete/<str:patient_id>/', views.patient_delete, name='patient_delete'),
    path('export/', views.patient_export, name='patient_export'),
    path('print/<str:patient_id>/', views.patient_print, name='patient_print'),
]