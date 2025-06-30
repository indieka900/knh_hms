from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import RegisterForm, LoginForm


def auth_view(request):
    """Combined login and register view"""
    login_form = LoginForm()
    register_form = RegisterForm()
    
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
        return redirect('dashboard')
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
        return redirect('dashboard')
    else:
        messages.error(request, "Please correct the errors below.")
    
    return render(request, 'auth.html', {
        'login_form': LoginForm(),
        'register_form': form
    })