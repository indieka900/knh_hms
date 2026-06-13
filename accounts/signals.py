# signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User
from patients.models import Patient

# NOTE: Doctor and BillingStaff/Pharmacist are created via admin/staff flows or PatientCreationForm.
# Signals provide minimal safe profiles on direct User role set or register (to prevent crashes).

@receiver(pre_save, sender=User)
def switch_user_role_cleanup(sender, instance, **kwargs):
    try:
        old = User.objects.get(pk=instance.pk)
        if old.role != instance.role:
            # Cleanup old role-specific model (avoid orphans)
            if old.role == 'doctor':
                from appointments.models import Doctor
                Doctor.objects.filter(user=old).delete()
            elif old.role == 'billing_staff':
                from billing.models import BillingStaff
                BillingStaff.objects.filter(user=old).delete()
            elif old.role == 'patient':
                Patient.objects.filter(user=old).delete()
            # pharmacist has no auto profile enforced in signals currently
    except User.DoesNotExist:
        pass

@receiver(post_save, sender=User)
def create_role_specific_model(sender, instance, **kwargs):
    # Lazy imports inside to avoid any import cycles at module load
    if instance.role == 'doctor':
        from appointments.models import Doctor
        Doctor.objects.get_or_create(user=instance, defaults={
            'specialization': 'General',
            'license_number': f"LIC{instance.id:05d}",
            'consultation_fee': 0.00
        })
    elif instance.role == 'billing_staff':
        from billing.models import BillingStaff
        BillingStaff.objects.get_or_create(user=instance, defaults={
            'staff_id': f"BILL{instance.id:05d}"
        })
    elif instance.role == 'patient':
        Patient.objects.get_or_create(user=instance, defaults={
            'patient_id': f"PAT{instance.id:06d}",
            'gender': 'O',
            'emergency_contact_name': 'N/A',
            'emergency_contact_phone': 'N/A',
            'emergency_contact_relationship': 'N/A',
        })
    # Pharmacist profile (if role used) can be created manually or extend here.
