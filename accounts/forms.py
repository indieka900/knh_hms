from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'id': 'loginEmail'
        })
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'id': 'loginPassword'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user = authenticate(self.request, email=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Invalid email or password")
        return self.cleaned_data

    def get_user(self):
        return self.user


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Create a password',
        'id': 'registerPassword'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Confirm your password',
        'id': 'confirmPassword'
    }))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password']

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Enter your first name', 'id': 'firstName'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Enter your last name', 'id': 'lastName'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input', 'placeholder': 'Enter your email', 'id': 'registerEmail'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'Enter your phone number', 'id': 'phoneNumber'
            }),
            # 'role': forms.Select(attrs={
            #     'class': 'form-select', 'id': 'userRole'
            # }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
