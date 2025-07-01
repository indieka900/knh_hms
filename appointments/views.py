from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.timezone import localdate
from datetime import datetime
from datetime import timedelta, timezone, date
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Appointment
from .forms import AppointmentForm
from patients.models import Patient
from .models import Appointment, Doctor



@login_required
def appointment_detail_view(request, appointment_id):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    user_is_doctor = hasattr(request.user, 'doctor')
    user_is_patient = hasattr(request.user, 'patient')
    
    can_view = False
    if user_is_doctor and appointment.doctor.user == request.user:
        can_view = True
    elif user_is_patient and appointment.patient.user == request.user:
        can_view = True
    elif request.user.is_staff:
        can_view = True
        
    if not can_view:
        messages.error(request, 'You do not have permission to view this appointment.')
        return redirect('appointments:appointments')
    
    context = {
        'appointment': appointment,
        'title': f'Appointment - {appointment.appointment_id}',
        'user_is_doctor': user_is_doctor,
        'user_is_patient': user_is_patient,
    }
    
    return render(request, 'appointment_detail.html', context)

@login_required
def appointment_list(request):
    user_is_doctor = hasattr(request.user, 'doctor')
    user_is_patient = hasattr(request.user, 'patient')

    if user_is_doctor:
        appointments = Appointment.objects.filter(
            doctor__user=request.user
        )
        title = "My Appointments (Doctor)"
    elif user_is_patient:
        appointments = Appointment.objects.filter(
            patient__user=request.user
        )
        title = "My Appointments"
    elif request.user.is_staff:
        appointments = Appointment.objects.all()
        title = "All Appointments"
    else:
        messages.error(request, 'You do not have permission to view appointments.')
        return redirect('home')

    # Filters
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    context = {
        'appointments': appointments.select_related('patient__user', 'doctor__user').order_by('-appointment_date', '-appointment_time'),
        'title': title,
        'user_is_doctor': user_is_doctor,
        'user_is_patient': user_is_patient,
        'status_choices': Appointment.STATUS_CHOICES,
        'current_status': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'doctors': Doctor.objects.select_related('user'),  # Needed for doctor filter
        'today_appointments': appointments.filter(appointment_date=today).count(),
        'pending_appointments': appointments.filter(status='scheduled').count(),
        'week_appointments': appointments.filter(appointment_date__range=(start_of_week, end_of_week)).count(),
        'completed_appointments': appointments.filter(status='completed').count(),
    }

    return render(request, 'appointments.html', context)

@login_required
def confirm_appointment_view(request, appointment_id):
    """Confirm an appointment"""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    # Check permissions (only doctor can confirm)
    if not (hasattr(request.user, 'doctor') and appointment.doctor.user == request.user):
        messages.error(request, 'Only the assigned doctor can confirm appointments.')
        return redirect('appointments:detail', appointment_id=appointment_id)
    
    if request.method == 'POST':
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, 'Appointment confirmed successfully.')
        
        # You could add email notification here
        # send_appointment_confirmation_email(appointment)
        
    return redirect('appointments:detail', appointment_id=appointment_id)

@login_required
def cancel_appointment_view(request, appointment_id):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    # Check permissions
    user_is_doctor = hasattr(request.user, 'doctor')
    user_is_patient = hasattr(request.user, 'patient')
    
    can_cancel = False
    if user_is_doctor and appointment.doctor.user == request.user:
        can_cancel = True
    elif user_is_patient and appointment.patient.user == request.user:
        can_cancel = True
    elif request.user.is_staff:
        can_cancel = True
        
    if not can_cancel:
        messages.error(request, 'You do not have permission to cancel this appointment.')
        return redirect('appointments:detail', appointment_id=appointment_id)
    
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason', '')
        appointment.status = 'cancelled'
        if reason:
            appointment.notes = f"Cancelled: {reason}\n{appointment.notes or ''}"
        appointment.save()
        
        messages.success(request, 'Appointment cancelled successfully.')
        
        # You could add email notification here
        # send_appointment_cancellation_email(appointment, reason)
        
        return redirect('appointments:appointments')
    
    context = {
        'appointment': appointment,
        'title': f'Cancel Appointment - {appointment.appointment_id}',
    }
    
    return render(request, 'appointment_cancel.html', context)

@login_required
def delete_appointment_view(request, appointment_id):
    """Delete an appointment (admin only or specific conditions)"""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    # Only staff or specific conditions can delete
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete appointments.')
        return redirect('appointments:detail', appointment_id=appointment_id)
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, 'Appointment deleted successfully.')
        return redirect('appointments:appointments')
    
    context = {
        'appointment': appointment,
        'title': f'Delete Appointment - {appointment.appointment_id}',
    }
    
    return render(request, 'appointment_delete.html', context)

def generate_appointment_id():
    timestamp = datetime.now().strftime('%Y%m%d')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"APT-{timestamp}-{unique_id}"

@login_required
def create_appointment_view(request):
    # Determine user role
    user_is_doctor = hasattr(request.user, 'doctor')
    user_is_patient = hasattr(request.user, 'patient')
    
    if not (user_is_doctor or user_is_patient):
        messages.error(request, 'You must be either a doctor or patient to create appointments.')
        return redirect('home')  # or appropriate redirect
    
    # Get current user's profile
    current_doctor = request.user.doctor if user_is_doctor else None
    current_patient = request.user.patient if user_is_patient else None
    
    # Get available options based on user role
    if user_is_doctor:
        # Doctor can select any patient
        patients = Patient.objects.select_related('user').filter(user__is_active=True)
        doctors = Doctor.objects.filter(id=current_doctor.id)  # Only current doctor
    else:
        # Patient can select any doctor
        doctors = Doctor.objects.select_related('user').filter(user__is_active=True)
        patients = Patient.objects.filter(patient_id=current_patient.patient_id)  # Only current patient
    
    if request.method == 'POST':
        post_data = request.POST.copy()

        if user_is_doctor:
            post_data['doctor'] = current_doctor.id
        else:
            post_data['patient'] = current_patient.patient_id

        form = AppointmentForm(post_data)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = 'scheduled'
            appointment.id = generate_appointment_id()

            
            # Auto-assign based on user role
            if user_is_doctor:
                appointment.doctor = current_doctor
            else:
                appointment.patient = current_patient
                
            appointment.save()
            messages.success(request, 'Appointment scheduled successfully.')
            return redirect('appointments:appointments')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-populate form based on user role
        initial_data = {}
        if user_is_doctor:
            initial_data['doctor'] = current_doctor.id
        else:
            initial_data['patient'] = current_patient.patient_id
            
        form = AppointmentForm(initial=initial_data)
   
    context = {
        'form': form,
        'doctors': doctors,
        'patients': patients,
        'title': 'Schedule New Appointment',
        'user_is_doctor': user_is_doctor,
        'user_is_patient': user_is_patient,
        'current_doctor': current_doctor,
        'current_patient': current_patient,
        'today': datetime.now().date(),
    }
    
    return render(request, 'appointment_edit.html', context)

@login_required
def edit_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    user_is_doctor = hasattr(request.user, 'doctor')
    user_is_patient = hasattr(request.user, 'patient')
    
    # Verify user can edit this appointment
    can_edit = False
    if user_is_doctor and appointment.doctor.user == request.user:
        can_edit = True
    elif user_is_patient and appointment.patient.user == request.user:
        can_edit = True
    elif request.user.is_staff:  # Admin can edit any appointment
        can_edit = True
        
    if not can_edit:
        messages.error(request, 'You do not have permission to edit this appointment.')
        return redirect('appointments:appointments')
    
    # Get current user's profile
    current_doctor = request.user.doctor if user_is_doctor else None
    current_patient = request.user.patient if user_is_patient else None
    
    # Get available options based on user role and edit permissions
    if user_is_doctor or request.user.is_staff:
        # Doctor or admin can change patient
        patients = Patient.objects.select_related('user').filter(user__is_active=True)
        doctors = Doctor.objects.select_related('user').filter(user__is_active=True)
    else:
        # Patient can only change doctor
        doctors = Doctor.objects.select_related('user').filter(user__is_active=True)
        patients = Patient.objects.filter(patient_id=appointment.patient.patient_id)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            updated_appointment = form.save(commit=False)
            
            # Ensure user can't change restricted fields
            if user_is_patient and not request.user.is_staff:
                # Patient can't change patient field
                updated_appointment.patient = appointment.patient
            elif user_is_doctor and not request.user.is_staff:
                # Doctor can't change doctor field (unless admin)
                updated_appointment.doctor = appointment.doctor
            appointment.status = request.POST.get('status', appointment.status)
            updated_appointment.save()
            messages.success(request, 'Appointment updated successfully.')
            return redirect('appointments:appointment_detail', appointment_id=appointment.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm(instance=appointment)
    
    # Get status choices for the form
    status_choices = Appointment.STATUS_CHOICES
    
    context = {
        'form': form,
        'object': appointment,
        'doctors': doctors,
        'patients': patients,
        'title': 'Edit Appointment',
        'user_is_doctor': user_is_doctor,
        'user_is_patient': user_is_patient,
        'current_doctor': current_doctor,
        'current_patient': current_patient,
        'status_choices': status_choices,
        'today': datetime.now().date(),
    }
    
    return render(request, 'appointment_edit.html', context)

@login_required
def check_appointment_conflicts(request):
    """AJAX endpoint to check for scheduling conflicts"""
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        patient_id = request.POST.get('patient')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        appointment_id = request.POST.get('appointment_id')
        
        conflicts = []
        
        if doctor_id and appointment_date and appointment_time:
            # Check doctor availability
            doctor_conflicts = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['scheduled', 'confirmed']
            )
            
            # Exclude current appointment if editing
            if appointment_id:
                doctor_conflicts = doctor_conflicts.exclude(id=appointment_id)
                
            if doctor_conflicts.exists():
                conflicts.append(f"Doctor already has an appointment at this time")
        
        if patient_id and appointment_date and appointment_time:
            # Check patient availability
            patient_conflicts = Appointment.objects.filter(
                patient_id=patient_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['scheduled', 'confirmed']
            )
            
            # Exclude current appointment if editing
            if appointment_id:
                patient_conflicts = patient_conflicts.exclude(id=appointment_id)
                
            if patient_conflicts.exists():
                conflicts.append(f"Patient already has an appointment at this time")
        
        return JsonResponse({'conflicts': conflicts})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_available_slots(request):
    """AJAX endpoint to get available time slots for a doctor on a specific date"""
    doctor_id = request.GET.get('doctor')
    date = request.GET.get('date')
    appointment_id = request.GET.get('appointment_id')  # For editing
    
    if not doctor_id or not date:
        return JsonResponse({'slots': []})
    
    # Get all possible time slots
    all_slots = [
        '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', 
        '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', 
        '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
    ]
    
    # Get booked slots for this doctor on this date
    booked_appointments = Appointment.objects.filter(
        doctor_id=doctor_id,
        appointment_date=date,
        status__in=['scheduled', 'confirmed']
    )
    
    # Exclude current appointment if editing
    if appointment_id:
        booked_appointments = booked_appointments.exclude(appointment_id=appointment_id)
    
    booked_slots = list(booked_appointments.values_list('appointment_time', flat=True))
    booked_slots = [slot.strftime('%H:%M') if hasattr(slot, 'strftime') else str(slot) for slot in booked_slots]
    
    # Return available slots
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    
    return JsonResponse({'slots': available_slots})

# Create your views here.
