from django.contrib.auth.models import AbstractUser
from django.db import models
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
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.role}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=100, blank=True)  # For doctors
    license_number = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact = models.CharField(max_length=17, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user.role}"