from django.contrib.auth.models import AbstractUser
from django.db import models
from accounts.managers import CustomUserManager
from django.core.validators import RegexValidator

class User(AbstractUser):
    USER_ROLES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('pharmacist', 'Pharmacist'),
        ('billing_staff', 'Billing Staff'),
        ('administrator', 'Administrator'),
    ]
    email = models.EmailField(unique=True)
    username = None
    role = models.CharField(max_length=20, choices=USER_ROLES, default='patient')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.role}"

    def has_module_permission(self, module):
        """Check if this user can access a given module (for sidebar + feature gating)."""
        if getattr(self, 'is_superuser', False) or self.role == 'administrator':
            return True
        return RolePermission.objects.filter(role=self.role, module=module, can_view=True).exists()
    
    # def get_role_profile(self):
    #     """Get the role-specific profile based on current role"""
    #     role_models = {
    #         'patient': Patient,
    #         'doctor': Doctor,
    #         'billing_staff': BillingStaff,
    #     }
        
    #     model_class = role_models.get(self.role)
    #     if model_class:
    #         try:
    #             return model_class.objects.get(user=self)
    #         except model_class.DoesNotExist:
    #             return None
    #     return None
    
    # def change_role(self, new_role, **role_specific_data):
    #     """Change user role and handle profile migration"""
    #     if new_role not in [choice[0] for choice in self.USER_ROLES]:
    #         raise ValueError(f"Invalid role: {new_role}")
        
    #     old_role = self.role
        
    #     if old_role != new_role:
    #         self._remove_from_old_role_model(old_role)
    #         self.role = new_role
    #         self.save()
    #         self._create_role_profile(new_role, **role_specific_data)
    
    # def _remove_from_old_role_model(self, old_role):
    #     """Remove user from old role-specific model"""
    #     role_models = {
    #         'doctor': Doctor,
    #         'billing_staff': BillingStaff,
    #         'patient': Patient,
    #     }
        
    #     old_model = role_models.get(old_role)
    #     if old_model:
    #         try:
    #             old_profile = old_model.objects.get(user=self)
    #             old_profile.delete()
    #         except old_model.DoesNotExist:
    #             pass
    
    # def _create_role_profile(self, new_role, **role_specific_data):
    #     """Create role-specific profile"""
    #     if new_role == 'patient':
    #         Patient.objects.create(user=self, **role_specific_data)
    #     elif new_role == 'doctor':
    #         Doctor.objects.create(user=self, **role_specific_data)
    #     elif new_role == 'billing_staff':
    #         BillingStaff.objects.create(user=self, **role_specific_data)


# Modules that can be permissioned in the sidebar / system
MODULE_CHOICES = [
    ('patients', 'Patients'),
    ('medical_records', 'Medical Records'),
    ('appointments', 'Appointments'),
    ('pharmacy', 'Pharmacy'),
    ('billing', 'Billing'),
    ('reports', 'Reports'),
    ('user_management', 'User Management'),
    ('system_settings', 'System Settings'),
]


class RolePermission(models.Model):
    """Stores which modules a given role is allowed to access (view in sidebar + features)."""
    role = models.CharField(max_length=20, choices=User.USER_ROLES)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    can_view = models.BooleanField(default=True)

    class Meta:
        unique_together = ('role', 'module')
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'

    def __str__(self):
        return f"{self.get_role_display()} → {self.get_module_display()} ({'allowed' if self.can_view else 'denied'})"

    @classmethod
    def get_default_permissions(cls):
        """Return sensible defaults for each role."""
        defaults = {
            'administrator': [m[0] for m in MODULE_CHOICES],  # all
            'doctor': ['patients', 'medical_records', 'appointments', 'reports'],
            'pharmacist': ['pharmacy', 'patients'],
            'billing_staff': ['billing', 'patients'],
            'patient': ['appointments'],  # patients have very limited; profile + own history are special cased
        }
        return defaults

    @classmethod
    def ensure_defaults(cls):
        """Seed default permissions if none exist for a role."""
        for role, modules in cls.get_default_permissions().items():
            for mod in modules:
                cls.objects.get_or_create(role=role, module=mod, defaults={'can_view': True})
