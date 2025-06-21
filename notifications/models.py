from django.db import models
from django.conf import settings

class NotificationTemplate(models.Model):
    NOTIFICATION_TYPES = [
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('payment_due', 'Payment Due'),
        ('prescription_ready', 'Prescription Ready'),
        ('test_results', 'Test Results Available'),
        ('system_alert', 'System Alert'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    subject = models.CharField(max_length=200)
    message_template = models.TextField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.type}"

class Notification(models.Model):
    NOTIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
        ('push', 'Push Notification'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS)
    status = models.CharField(max_length=10, choices=NOTIFICATION_STATUS, default='pending')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.subject} - {self.recipient.get_full_name()}"