# signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User
from appointments.models import Doctor
from billing.models import BillingStaff
from patients.models import Patient

@receiver(post_save, sender=User)
def create_patient_by_default(sender, instance, created, **kwargs):
    if created and instance.role == 'patient':
        Patient.objects.get_or_create(user=instance, defaults={
            'patient_id': f"PAT{instance.id:05d}",
            'gender': 'O',
            'emergency_contact_name': '',
            'emergency_contact_phone': '',
            'emergency_contact_relationship': '',
        })

@receiver(pre_save, sender=User)
def switch_user_role_cleanup(sender, instance, **kwargs):
    try:
        old = User.objects.get(pk=instance.pk)
        if old.role != instance.role:
            # Cleanup old role-specific model
            if old.role == 'doctor':
                Doctor.objects.filter(user=old).delete()
            elif old.role == 'billing_staff':
                BillingStaff.objects.filter(user=old).delete()
            elif old.role == 'patient':
                Patient.objects.filter(user=old).delete()
    except User.DoesNotExist:
        pass

@receiver(post_save, sender=User)
def create_role_specific_model(sender, instance, **kwargs):
    if instance.role == 'doctor':
        Doctor.objects.get_or_create(user=instance, defaults={
            'specialization': '',
            'license_number': f"LIC{instance.id:05d}",
            'consultation_fee': 0.00
        })
    elif instance.role == 'billing_staff':
        BillingStaff.objects.get_or_create(user=instance, defaults={
            'staff_id': f"BILL{instance.id:05d}"
        })
    elif instance.role == 'patient':
        Patient.objects.get_or_create(user=instance, defaults={
            'patient_id': f"PAT{instance.id:05d}",
            'gender': 'O',
            'emergency_contact_name': '',
            'emergency_contact_phone': '',
            'emergency_contact_relationship': '',
        })
