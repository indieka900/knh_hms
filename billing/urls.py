from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Dashboard
    path('', views.billing_dashboard, name='billing_dashboard'),
    
    # Bills Management
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/create/', views.create_bill, name='create_bill'),
    path('bills/<str:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bills/<str:bill_id>/edit/', views.edit_bill, name='edit_bill'),
    path('bills/<str:bill_id>/print/', views.print_bill, name='print_bill'),
    
    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/process/<str:bill_id>/', views.process_payment, name='process_payment'),
    path('payments/<str:payment_id>/', views.payment_detail, name='payment_detail'),
    
    # Service Types
    path('services/', views.service_type_list, name='service_type_list'),
    path('services/create/', views.create_service_type, name='create_service_type'),
    path('services/<int:service_id>/edit/', views.edit_service_type, name='edit_service_type'),
    
    # Reports
    path('reports/', views.billing_reports, name='billing_reports'),
    path('reports/revenue/', views.revenue_report, name='revenue_report'),
    
    # API endpoints for AJAX
    path('api/patient-bills/<str:patient_id>/', views.get_patient_bills, name='get_patient_bills'),
    path('api/bill-calculate/', views.calculate_bill_total, name='calculate_bill_total'),
]