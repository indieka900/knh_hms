from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, UserProfileForm


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
    """Allow any logged-in user to view and update their own profile (name, contact info, DOB, address, picture)."""
    user = request.user

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=user)

    context = {
        'title': 'My Profile',
        'form': form,
        'user': user,
    }
    return render(request, 'profile.html', context)


from django.contrib.auth.decorators import user_passes_test
from .models import RolePermission, MODULE_CHOICES, User

def is_administrator(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'administrator')

@login_required
@user_passes_test(is_administrator)
def role_permissions_view(request):
    """Admin interface to assign module view permissions to roles."""
    # Ensure defaults exist
    RolePermission.ensure_defaults()

    roles = [r for r in User.USER_ROLES if r[0] != 'patient']  # patients have very limited hard-coded access
    # For completeness we can include patient too
    all_roles = list(User.USER_ROLES)

    if request.method == 'POST':
        selected_role = request.POST.get('role')
        if selected_role:
            # Remove old permissions for this role
            RolePermission.objects.filter(role=selected_role).delete()

            # Add the checked ones
            checked_modules = request.POST.getlist('modules')
            for mod in checked_modules:
                RolePermission.objects.create(role=selected_role, module=mod, can_view=True)

            messages.success(request, f"Permissions updated for role: {dict(User.USER_ROLES).get(selected_role, selected_role)}")
            return redirect('accounts:role_permissions')

        # Handle "Reset to defaults" action
        if request.POST.get('action') == 'reset_defaults':
            RolePermission.objects.all().delete()
            RolePermission.ensure_defaults()
            messages.success(request, "Permissions have been reset to sensible defaults.")
            return redirect('accounts:role_permissions')

    # For GET: prepare current state per role for the template
    role_data = []
    for role_code, role_label in all_roles:
        current = list(
            RolePermission.objects.filter(role=role_code, can_view=True)
            .values_list('module', flat=True)
        )
        role_data.append({
            'code': role_code,
            'label': role_label,
            'current_modules': current,
        })

    context = {
        'title': 'Role Permissions',
        'role_data': role_data,
        'modules': MODULE_CHOICES,
        'selected_role': request.GET.get('role') or (role_data[0]['code'] if role_data else ''),
    }
    return render(request, 'role_permissions.html', context)