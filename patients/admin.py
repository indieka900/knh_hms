from django.contrib import admin
from patients.models import Patient, PatientVitals

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'user', 'gender', 'blood_group')
    list_filter = ('gender', 'blood_group')
    search_fields = ('patient_id', 'user__email', 'user__first_name', 'user__last_name')

admin.site.register(PatientVitals)

# Register your models here.
