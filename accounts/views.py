from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm


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