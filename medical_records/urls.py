from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    # Dashboard
    path('', views.medical_records_dashboard, name='medical_records_dashboard'),
    
    # Medical Records
    path('records/', views.medical_record_list, name='medical_record_list'),
    path('records/create/<str:patient_id>/', views.create_medical_record, name='create_medical_record'),
    path('records/<str:record_id>/', views.medical_record_detail, name='medical_record_detail'),
    path('records/<str:record_id>/edit/', views.edit_medical_record, name='edit_medical_record'),
    path('records/<str:record_id>/print/', views.print_medical_record, name='print_medical_record'),
    
    # Patient Records Overview
    path('patient/<str:patient_id>/', views.patient_medical_history, name='patient_medical_history'),
    
    # Prescriptions
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/create/<str:record_id>/', views.create_prescription, name='create_prescription'),
    path('prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/<int:prescription_id>/edit/', views.edit_prescription, name='edit_prescription'),
    
    # Lab Tests
    path('lab-tests/', views.lab_test_list, name='lab_test_list'),
    path('lab-tests/create/<str:record_id>/', views.create_lab_test, name='create_lab_test'),
    path('lab-tests/<int:test_id>/', views.lab_test_detail, name='lab_test_detail'),
    path('lab-tests/<int:test_id>/edit/', views.edit_lab_test, name='edit_lab_test'),
    path('lab-tests/<int:test_id>/results/', views.update_lab_results, name='update_lab_results'),
    
    # Vitals
    path('vitals/record/<str:patient_id>/', views.record_vitals, name='record_vitals'),
    path('vitals/<str:patient_id>/history/', views.vitals_history, name='vitals_history'),
    
    # API endpoints
    path('api/patient-search/', views.patient_search, name='patient_search'),
    path('api/medical-history/<str:patient_id>/', views.get_medical_history, name='get_medical_history'),
    path('api/prescription-template/', views.get_prescription_template, name='get_prescription_template'),
]