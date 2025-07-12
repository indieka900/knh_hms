from django.urls import path
from .views import (
    pharmacy_dashboard,
    pharmacy_dashboard_data,
    patients_api,
    inventory_api,
    update_stock_api,
    dispensing_api,
    # patient_list_api,
    # prescription_list_api,
    # inventory_list_api,
    # dispensing_history_api,
)

app_name = 'pharmacy'

urlpatterns = [
    path('', pharmacy_dashboard, name='pharmacy_dashboard'),
    path('api/pharmacy-dashboard-data/', pharmacy_dashboard_data, name='pharmacy_dashboard_data'),
    path('api/patients/', patients_api, name='patients_api'),
    path('api/inventory/', inventory_api, name='inventory_api'),
    path('api/inventory/<int:item_id>/update-stock/', update_stock_api, name='update_stock_api'),
    path('api/dispense/', dispensing_api, name='dispensing_api'),
    path('api/patient-list/', patients_api, name='patient_list_api'),
    # path('api/prescriptions/', prescription_list_api, name='prescription_list_api'),
    # path('api/inventory-list/', inventory_list_api, name='inventory_list_api'),
    # path('api/dispensing-history/', dispensing_history_api, name='dispensing_history_api'),
]
