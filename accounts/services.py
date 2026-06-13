from django.contrib.auth import get_user_model

User = get_user_model()

# Lazy imports inside functions to avoid cycles and missing names on User model.
# Role changes are intentionally simple (set role; signals + admin forms handle profile creation).

class RoleManager:
    """Utility class for managing user roles (minimal working version)."""
    
    @staticmethod
    def promote_to_doctor(user, admin_user, specialization, license_number, 
                        consultation_fee, years_of_experience=0):
        """Promote a user to doctor role (sets role; profile created via signals or forms)."""
        if not admin_user.is_staff and getattr(admin_user, 'role', None) != 'administrator':
            raise PermissionError("Only administrators can change user roles")
        user.role = 'doctor'
        user.save()
        # Signals will attempt minimal Doctor profile
        from appointments.models import Doctor
        doc, _ = Doctor.objects.get_or_create(
            user=user,
            defaults={'specialization': specialization or 'General', 'license_number': license_number or f'LIC{user.id:05d}', 'consultation_fee': consultation_fee or 0}
        )
        return doc
    
    @staticmethod
    def promote_to_billing_staff(user, admin_user, staff_id=None):
        if not admin_user.is_staff and getattr(admin_user, 'role', None) != 'administrator':
            raise PermissionError("Only administrators can change user roles")
        user.role = 'billing_staff'
        user.save()
        from billing.models import BillingStaff
        bs, _ = BillingStaff.objects.get_or_create(
            user=user,
            defaults={'staff_id': staff_id or f'BILL{user.id:05d}'}
        )
        return bs
    
    @staticmethod
    def demote_to_patient(user, admin_user):
        if not admin_user.is_staff and getattr(admin_user, 'role', None) != 'administrator':
            raise PermissionError("Only administrators can change user roles")
        user.role = 'patient'
        user.save()
        from patients.models import Patient
        pat, _ = Patient.objects.get_or_create(
            user=user,
            defaults={'gender': 'O', 'emergency_contact_name': 'N/A', 'emergency_contact_phone': 'N/A', 'emergency_contact_relationship': 'N/A'}
        )
        return pat
    
    @staticmethod
    def get_users_by_role(role):
        return User.objects.filter(role=role)
    
    @staticmethod
    def get_role_statistics():
        from django.db.models import Count
        return User.objects.values('role').annotate(count=Count('role'))


class UserService:
    """Service class for user-related operations (fixed for email-only user + no username)."""
    
    @staticmethod
    def create_patient(email, password, **patient_data):
        """Create a new patient user (no username; email is USERNAME_FIELD)."""
        user = User.objects.create_user(
            email=email,
            password=password,
            role='patient'
        )
        # Profile mostly handled by signals now. Apply extra if provided.
        if patient_data:
            from patients.models import Patient
            try:
                patient = Patient.objects.get(user=user)
                for key, value in patient_data.items():
                    if hasattr(patient, key):
                        setattr(patient, key, value)
                patient.save()
            except Patient.DoesNotExist:
                pass
        return user
    
    @staticmethod
    def get_user_profile_data(user):
        """Get complete user profile data including role-specific info."""
        profile = None
        try:
            if user.role == 'patient':
                from patients.models import Patient
                profile = Patient.objects.filter(user=user).first()
            elif user.role == 'doctor':
                from appointments.models import Doctor
                profile = Doctor.objects.filter(user=user).first()
            elif user.role == 'billing_staff':
                from billing.models import BillingStaff
                profile = BillingStaff.objects.filter(user=user).first()
        except Exception:
            profile = None
        return {
            'user': user,
            'role_profile': profile,
            'role_type': user.role
        }