from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Patient

User = get_user_model()

class PatientCreationForm(forms.ModelForm):
    """Form for creating a new patient with user account"""
    
    # User fields
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    phone_number = forms.CharField(
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890'
        })
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter full address'
        }),
        required=False
    )
    
    # Password fields
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    
    class Meta:
        model = Patient
        fields = [
            'gender', 'blood_group', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship',
            'insurance_provider', 'insurance_number', 'allergies',
            'chronic_conditions'
        ]
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact full name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Spouse, Parent, Sibling'
            }),
            'insurance_provider': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Insurance company name'
            }),
            'insurance_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Insurance policy number'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List any known allergies'
            }),
            'chronic_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List any chronic medical conditions'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match.")
        
        return cleaned_data
    
    def save(self, commit=True):
        # Create user first
        user = User(
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            phone_number=self.cleaned_data['phone_number'],
            date_of_birth=self.cleaned_data['date_of_birth'],
            address=self.cleaned_data['address'],
            role='patient'
        )
        print("Creating user with email:", user.email)  # Debugging line
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
            print("User created successfully:", user.email)
            patient = super().save(commit=False)
            patient.user = user
            patient.save()
            
            return patient
        
        return user