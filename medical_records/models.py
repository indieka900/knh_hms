from django.db import models
from django.conf import settings
from patients.models import Patient
from appointments.models import Doctor, Appointment

class MedicalRecord(models.Model):
    record_id = models.CharField(max_length=20, unique=True, primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    diagnosis = models.TextField()
    symptoms = models.TextField()
    treatment_plan = models.TextField()
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Record {self.record_id} - {self.patient.user.get_full_name()}"

class Prescription(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    instructions = models.TextField(blank=True)
    is_dispensed = models.BooleanField(default=False)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    dispensed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.medication_name} - {self.medical_record.patient.user.get_full_name()}"

class LabTest(models.Model):
    TEST_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='lab_tests')
    test_name = models.CharField(max_length=100)
    test_description = models.TextField()
    status = models.CharField(max_length=15, choices=TEST_STATUS, default='pending')
    results = models.TextField(blank=True)
    test_date = models.DateTimeField(null=True, blank=True)
    result_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.test_name} - {self.medical_record.patient.user.get_full_name()}"