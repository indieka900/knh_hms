from django.urls import path
from appointments import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointments'),
    path('create/', views.create_appointment_view, name='appointment_create'),
    path('edit/<str:appointment_id>/', views.edit_appointment_view, name='appointment_edit'),
    # path('delete/<str:appointment_id>/', views.appointment_delete, name='appointment_delete'),
    # path('detail/<str:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    # path('search/', views.appointment_search, name='appointment_search'),
]