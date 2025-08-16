from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import User
from patients.models import Patient
from appointments.models import Doctor
from billing.models import BillingStaff
from pharmacy.models import Pharmacist


def auth_view(request):
    """Combined login and register view"""
    login_form = LoginForm()
    register_form = RegisterForm()
    
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        if 'login' in request.POST:
            return handle_login(request)
        elif 'register' in request.POST:
            return handle_register(request)
    
    return render(request, 'auth.html', {
        'login_form': login_form,
        'register_form': register_form
    })


def handle_login(request):
    form = LoginForm(request, request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "Login successful. Welcome back!")
        return redirect('dashboard:dashboard')
    else:
        messages.error(request, "Invalid email or password.")
    
    return render(request, 'auth.html', {
        'login_form': form,
        'register_form': RegisterForm()
    })



def handle_register(request):
    """Handle registration form submission"""
    form = RegisterForm(request.POST)
    
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Registration successful. You are now logged in.")
        return redirect('dashboard:dashboard')
    else:
        messages.error(request, "Please correct the errors below.")
    
    return render(request, 'auth.html', {
        'login_form': LoginForm(),
        'register_form': form
    })
    

@login_required
def custom_logout_view(request):
    """Custom logout view to handle GET requests"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')

@login_required
def profile_view(request):
    """Display user profile with role-specific information"""
    user = request.user
    context = {
        'user': user,
        'title': 'My Profile'
    }
    
    # Get role-specific profile data
    role_profile = None
    try:
        if user.role == 'patient':
            role_profile = Patient.objects.get(user=user)
        elif user.role == 'doctor':
            role_profile = Doctor.objects.get(user=user)
        elif user.role == 'billing_staff':
            role_profile = BillingStaff.objects.get(user=user)
        elif user.role == 'pharmacist':
            role_profile = Pharmacist.objects.get(user=user)
    except:
        role_profile = None
    
    context['role_profile'] = role_profile
    
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit_view(request):
    """Edit user profile"""
    user = request.user
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileEditForm(instance=user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form, 'user': user})

@login_required
def settings_view(request):
    """User settings and preferences"""
    user = request.user
    
    if request.method == 'POST':
        # Handle password change
        if 'change_password' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully!')
                return redirect('accounts:login')
        
        # Handle notification preferences
        elif 'update_preferences' in request.POST:
            # Here you can add logic for notification preferences
            # For now, just show success message
            messages.success(request, 'Preferences updated successfully!')
    
    return render(request, 'accounts/settings.html', {'user': user})