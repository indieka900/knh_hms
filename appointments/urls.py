from django.urls import path
from appointments import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointments'),
    path('create/', views.create_appointment_view, name='appointment_create'),
    path('check-conflicts/', views.check_appointment_conflicts, name='check_conflicts'),
    path('available-slots/', views.get_available_slots, name='available_slots'),
    path('edit/<str:appointment_id>/', views.edit_appointment_view, name='appointment_edit'),
    path('<str:appointment_id>/', views.appointment_detail_view, name='detail'),
    # path('<str:appointment_id>/edit/', views.edit_appointment_view, name='edit'),
    path('<str:appointment_id>/delete/', views.delete_appointment_view, name='delete'),
    
    
    # Additional views
    path('<str:appointment_id>/confirm/', views.confirm_appointment_view, name='confirm'),
    path('<str:appointment_id>/cancel/', views.cancel_appointment_view, name='cancel'),
    # path('delete/<str:appointment_id>/', views.appointment_delete, name='appointment_delete'),
    # path('detail/<str:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    # path('search/', views.appointment_search, name='appointment_search'),
]