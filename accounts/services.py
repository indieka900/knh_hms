from django.contrib.auth import get_user_model
from .models import Doctor, Patient, BillingStaff

User = get_user_model()

class RoleManager:
    """Utility class for managing user roles"""
    
    @staticmethod
    def promote_to_doctor(user, admin_user, specialization, license_number, 
                        consultation_fee, years_of_experience=0):
        """Promote a user to doctor role"""
        if not admin_user.is_staff and admin_user.role != 'administrator':
            raise PermissionError("Only administrators can change user roles")
        
        user.change_role('doctor',
                        specialization=specialization,
                        license_number=license_number,
                        consultation_fee=consultation_fee,
                        years_of_experience=years_of_experience)
        return user.get_role_profile()
    
    @staticmethod
    def promote_to_billing_staff(user, admin_user, staff_id=None):
        """Promote a user to billing staff role"""
        if not admin_user.is_staff and admin_user.role != 'administrator':
            raise PermissionError("Only administrators can change user roles")
        
        user.change_role('billing_staff', staff_id=staff_id)
        return user.get_role_profile()
    
    @staticmethod
    def demote_to_patient(user, admin_user):
        """Demote a user back to patient role"""
        if not admin_user.is_staff and admin_user.role != 'administrator':
            raise PermissionError("Only administrators can change user roles")
        
        user.change_role('patient')
        return user.get_role_profile()
    
    @staticmethod
    def get_users_by_role(role):
        """Get all users with a specific role"""
        return User.objects.filter(role=role)
    
    @staticmethod
    def get_role_statistics():
        """Get statistics about user roles"""
        from django.db.models import Count
        return User.objects.values('role').annotate(count=Count('role'))


class UserService:
    """Service class for user-related operations"""
    
    @staticmethod
    def create_patient(email, username, password, **patient_data):
        """Create a new patient user"""
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='patient'
        )
        
        # Update patient profile with additional data
        if patient_data:
            patient = user.get_role_profile()
            for key, value in patient_data.items():
                if hasattr(patient, key):
                    setattr(patient, key, value)
            patient.save()
        
        return user
    
    @staticmethod
    def get_user_profile_data(user):
        """Get complete user profile data including role-specific info"""
        profile = user.get_role_profile()
        return {
            'user': user,
            'role_profile': profile,
            'role_type': user.role
        }