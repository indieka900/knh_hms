from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:pk>/', views.notification_detail, name='notification_detail'),
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('send/', views.create_notification, name='create_notification'),
    # AJAX
    path('api/mark-read/<int:pk>/', views.mark_read_ajax, name='mark_read_ajax'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
]
