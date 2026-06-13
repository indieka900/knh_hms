from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import RolePermission, MODULE_CHOICES


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
    role_profile = None
    try:
        if request.user.role == 'patient':
            from patients.models import Patient
            role_profile = Patient.objects.filter(user=request.user).first()
    except Exception:
        pass
    return render(request, 'accounts/profile.html', {
        'title': 'My Profile',
        'role_profile': role_profile,
    })


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.address = request.POST.get('address', user.address)
        dob = request.POST.get('date_of_birth')
        if dob:
            user.date_of_birth = dob
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('accounts:profile')
    return render(request, 'accounts/profile_edit.html', {'title': 'Edit Profile'})


@login_required
def settings_view(request):
    if request.method == 'POST':
        if 'change_password' in request.POST:
            current = request.POST.get('current_password')
            new_pw = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')
            if not request.user.check_password(current):
                messages.error(request, "Current password is incorrect.")
            elif new_pw != confirm:
                messages.error(request, "New passwords do not match.")
            elif len(new_pw) < 8:
                messages.error(request, "Password must be at least 8 characters.")
            else:
                request.user.set_password(new_pw)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password changed successfully.")
        else:
            messages.success(request, "Preferences saved.")
        return redirect('accounts:settings')
    return render(request, 'accounts/settings.html', {'title': 'Account Settings'})


@login_required
def role_permissions_view(request):
    if request.user.role != 'administrator' and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('dashboard:dashboard')

    roles = [r[0] for r in request.user.USER_ROLES]
    if request.method == 'POST':
        RolePermission.objects.all().delete()
        for role in roles:
            for module, _ in MODULE_CHOICES:
                key = f"{role}_{module}"
                RolePermission.objects.get_or_create(
                    role=role, module=module,
                    defaults={'can_view': key in request.POST}
                )
        messages.success(request, "Permissions updated.")
        return redirect('accounts:role_permissions')

    permissions = {r: {} for r in roles}
    for perm in RolePermission.objects.all():
        permissions[perm.role][perm.module] = perm.can_view

    return render(request, 'dashboard/user_management.html', {
        'title': 'Role Permissions',
        'roles': roles,
        'modules': MODULE_CHOICES,
        'permissions': permissions,
    })