from django.contrib import admin
from appointments.models import (Doctor, DoctorSchedule, Appointment)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number', 'consultation_fee', 'is_available')
    list_filter = ('specialization', 'is_available')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'license_number')
    search_fields = ('staff_id', 'user__email', 'user__first_name', 'user__last_name')

admin.site.register(DoctorSchedule)
admin.site.register(Appointment)

# Register your models here.
