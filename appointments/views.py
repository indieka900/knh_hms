from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.timezone import localdate
from datetime import timedelta
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Appointment
from .forms import AppointmentForm
from patients.models import Patient
from .models import Appointment, Doctor


def appointment_list(request):
    user = request.user
    today = localdate()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Base queryset
    if hasattr(user, 'doctor'):
        appointments = Appointment.objects.filter(doctor=user.doctor)
    elif hasattr(user, 'patient'):
        appointments = Appointment.objects.filter(patient=user.patient)
    else:
        appointments = Appointment.objects.all()

    # Filtering
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    doctor_filter = request.GET.get('doctor', '')
    date_filter = request.GET.get('date', '')

    if search_query:
        appointments = appointments.filter(
            Q(reason__icontains=search_query) |
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(doctor__user__first_name__icontains=search_query) |
            Q(doctor__user__last_name__icontains=search_query) |
            Q(appointment_id__icontains=search_query)
        )

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if doctor_filter:
        appointments = appointments.filter(doctor__doctor_id=doctor_filter)

    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    # Dashboard data
    today_appointments = appointments.filter(appointment_date=today).count()
    pending_appointments = appointments.filter(status='scheduled').count()
    week_appointments = appointments.filter(
        appointment_date__range=(start_of_week, end_of_week)
    ).count()
    completed_appointments = appointments.filter(
        status='completed', appointment_date__month=today.month
    ).count()

    # Pagination
    paginator = Paginator(appointments.order_by('-appointment_date', '-appointment_time'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Doctor list for filter dropdown
    doctors = Doctor.objects.select_related('user').all()

    context = {
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'doctors': doctors,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'week_appointments': week_appointments,
        'completed_appointments': completed_appointments,
    }
    return render(request, 'appointments.html', context)

def generate_appointment_id():
    return str(uuid.uuid4())[:8].upper()

def create_appointment_view(request):
    doctors = Doctor.objects.select_related('user').all()
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.appointment_id = generate_appointment_id()
            appointment.save()
            messages.success(request, 'Appointment created successfully.')
            return redirect('appointments:appointments')  # or wherever list view is
    else:
        form = AppointmentForm()
    
    return render(request, 'appointment_edit.html', {
        'form': form,
        'doctors' : doctors,
        'title': 'Create Appointment'
    })


def edit_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully.')
            return redirect('appointments:appointments')
    else:
        form = AppointmentForm(instance=appointment)
    
    return render(request, 'appointment_edit.html', {
        'form': form,
        'title': 'Edit Appointment'
    })

# Create your views here.
