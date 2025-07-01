from django.contrib import admin
from notifications.models import Notification, NotificationTemplate

admin.site.register(Notification)
admin.site.register(NotificationTemplate)

# Register your models here.
