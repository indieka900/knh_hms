from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import date, timedelta
import csv
import json
from .forms import PatientCreationForm
from .models import Patient
from appointments.models import Appointment
from medical_records.models import MedicalRecord
from billing.models import Bill

@login_required
def create_patient(request):
    """Create a new patient - only accessible by doctors and staff"""
    
    # Check if user has permission to create patients
    if not request.user.role in ['doctor', 'administrator', 'billing_staff']:
        messages.error(request, "You don't have permission to create patients.")
        return redirect('/')
    
    if request.method == 'POST':
        form = PatientCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    patient = form.save()
                    messages.success(
                        request, 
                        f"Patient {patient.user.get_full_name()} created successfully! "
                        f"Patient ID: {patient.patient_id}"
                    )
                    
                    # If this is an AJAX request (for modal), return JSON response
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'patient_id': patient.patient_id,
                            'patient_name': patient.user.get_full_name(),
                            'message': 'Patient created successfully!'
                        })
                    
                    # Regular form submission
                    return redirect('/')
                    
            except Exception as e:
                messages.error(request, f"Error creating patient: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
        else:
            # If AJAX request with form errors
            print(form.errors)  # Log form errors for debugging
            messages.error(request, "Please correct the errors below.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = PatientCreationForm()
    
    context = {
        'form': form,
        'title': 'Create New Patient'
    }
    
    # If AJAX request for modal content
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'create_patient_modal.html', context)
    
    return render(request, 'create_patient.html', context)


@login_required
@require_http_methods(["GET"])
def patient_search_ajax(request):
    """AJAX endpoint for patient search autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'patients': []})
    
    patients = Patient.objects.filter(
        user__first_name__icontains=query
    ).union(
        Patient.objects.filter(user__last_name__icontains=query)
    ).union(
        Patient.objects.filter(user__email__icontains=query)
    ).union(
        Patient.objects.filter(patient_id__icontains=query)
    )[:10]
    
    patient_data = [{
        'id': patient.patient_id,
        'name': patient.user.get_full_name(),
        'email': patient.user.email,
        'patient_id': patient.patient_id
    } for patient in patients]
    
    return JsonResponse({'patients': patient_data})

from datetime import date

@login_required
def patient_list(request):
    """Enhanced patient list with search, filter and pagination"""
    
    if not request.user.role in ['doctor', 'administrator', 'billing_staff']:
        messages.error(request, "You don't have permission to view patients.")
        return redirect('/')
    
    # Base queryset with related data
    patients = Patient.objects.select_related('user').prefetch_related('appointments', 'medical_records', 'bills')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        patients = patients.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(patient_id__icontains=search_query) |
            Q(user__phone_number__icontains=search_query)
        )
    
    # Filter by gender
    gender_filter = request.GET.get('gender', '')
    if gender_filter:
        patients = patients.filter(gender=gender_filter)
    
    # Filter by blood group
    blood_group_filter = request.GET.get('blood_group', '')
    if blood_group_filter:
        patients = patients.filter(blood_group=blood_group_filter)
    
    # Filter by registration date
    date_filter = request.GET.get('date_filter', '')
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            patients = patients.filter(created_at__date=today)
        elif date_filter == 'week':
            patients = patients.filter(created_at__date__gte=today - timedelta(days=7))
        elif date_filter == 'month':
            patients = patients.filter(created_at__date__gte=today - timedelta(days=30))
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        patients = patients.order_by('user__last_name', 'user__first_name')
    elif sort_by == 'date':
        patients = patients.order_by('-created_at')
    elif sort_by == 'id':
        patients = patients.order_by('patient_id')
    
    # Calculate ages and additional stats
    for patient in patients:
        if patient.user.date_of_birth:
            today = date.today()
            patient.calculated_age = today.year - patient.user.date_of_birth.year - ((today.month, today.day) < (patient.user.date_of_birth.month, patient.user.date_of_birth.day))
        else:
            patient.calculated_age = None
        
        # Add quick stats
        patient.appointment_count = patient.appointments.count()
        patient.medical_record_count = patient.medical_records.count()
        patient.outstanding_bills = patient.bills.filter(status__in=['pending', 'overdue']).count()
    
    # Pagination
    page_size = request.GET.get('per_page', 25)
    try:
        page_size = int(page_size)
        if page_size not in [10, 25, 50, 100]:
            page_size = 25
    except (ValueError, TypeError):
        page_size = 25
    
    paginator = Paginator(patients, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_patients = Patient.objects.count()
    new_this_month = Patient.objects.filter(
        created_at__gte=timezone.now().replace(day=1)
    ).count()
    
    context = {
        'page_obj': page_obj,
        'patients': page_obj.object_list,
        'title': 'Patient Management',
        'search_query': search_query,
        'gender_filter': gender_filter,
        'blood_group_filter': blood_group_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
        'per_page': page_size,
        'total_patients': total_patients,
        'new_this_month': new_this_month,
        'blood_groups': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        'gender_choices': [('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
    }
    
    return render(request, 'patient_list.html', context)

@login_required
def patient_detail(request, patient_id):
    """View detailed patient information"""
    
    if not request.user.role in ['doctor', 'administrator', 'billing_staff']:
        messages.error(request, "You don't have permission to view patient details.")
        return redirect('patients:patient_list')
    
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    # Calculate age
    if patient.user.date_of_birth:
        today = date.today()
        age = today.year - patient.user.date_of_birth.year - ((today.month, today.day) < (patient.user.date_of_birth.month, patient.user.date_of_birth.day))
    else:
        age = None
    
    # Get related records
    recent_appointments = patient.appointments.order_by('-appointment_date', '-appointment_time')[:5]
    recent_medical_records = patient.medical_records.order_by('-created_at')[:5]
    outstanding_bills = patient.bills.filter(status__in=['pending', 'overdue']).order_by('-created_at')
    
    context = {
        'patient': patient,
        'age': age,
        'recent_appointments': recent_appointments,
        'recent_medical_records': recent_medical_records,
        'outstanding_bills': outstanding_bills,
        'title': f'Patient Details - {patient.user.get_full_name()}'
    }
    
    return render(request, 'patient_detail.html', context)

@login_required
def patient_edit(request, patient_id):
    """Edit patient information"""
    
    if not request.user.role in ['doctor', 'administrator']:
        messages.error(request, "You don't have permission to edit patients.")
        return redirect('patients:patient_list')
    
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    if request.method == 'POST':
        # Update patient information
        user = patient.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone_number = request.POST.get('phone_number', '')
        user.address = request.POST.get('address', '')
        
        # Handle date of birth
        dob = request.POST.get('date_of_birth')
        if dob:
            try:
                from datetime import datetime
                user.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return render(request, 'patient_edit.html', {'patient': patient})
        
        # Update patient-specific fields
        patient.gender = request.POST.get('gender', '')
        patient.blood_group = request.POST.get('blood_group', '')
        patient.emergency_contact_name = request.POST.get('emergency_contact_name', '')
        patient.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
        patient.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', '')
        patient.insurance_provider = request.POST.get('insurance_provider', '')
        patient.insurance_number = request.POST.get('insurance_number', '')
        patient.allergies = request.POST.get('allergies', '')
        patient.chronic_conditions = request.POST.get('chronic_conditions', '')
        
        try:
            user.save()
            patient.save()
            messages.success(request, f'Patient {patient.user.get_full_name()} updated successfully!')
            return redirect('patients:patient_detail', patient_id=patient.patient_id)
        except Exception as e:
            messages.error(request, f'Error updating patient: {str(e)}')
    
    context = {
        'patient': patient,
        'title': f'Edit Patient - {patient.user.get_full_name()}',
        'blood_groups': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        'gender_choices': [('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
    }
    
    return render(request, 'patient_edit.html', context)

@login_required
@require_http_methods(["POST"])
def patient_delete(request, patient_id):
    """Delete a patient (admin only)"""
    
    if request.user.role != 'administrator':
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        patient = get_object_or_404(Patient, patient_id=patient_id)
        patient_name = patient.user.get_full_name()
        
        # Delete the user (which will cascade to patient)
        patient.user.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Patient {patient_name} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def patient_export(request):
    """Export patients to CSV"""
    
    if not request.user.role in ['doctor', 'administrator']:
        messages.error(request, "You don't have permission to export patient data.")
        return redirect('patients:patient_list')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="patients_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Patient ID', 'First Name', 'Last Name', 'Email', 'Phone', 
        'Gender', 'Blood Group', 'Date of Birth', 'Address',
        'Emergency Contact', 'Emergency Phone', 'Insurance Provider',
        'Registration Date'
    ])
    
    patients = Patient.objects.select_related('user').all()
    for patient in patients:
        writer.writerow([
            patient.patient_id,
            patient.user.first_name,
            patient.user.last_name,
            patient.user.email,
            patient.user.phone_number,
            patient.get_gender_display(),
            patient.blood_group,
            patient.user.date_of_birth,
            patient.user.address,
            patient.emergency_contact_name,
            patient.emergency_contact_phone,
            patient.insurance_provider,
            patient.created_at.strftime('%Y-%m-%d') if patient.created_at else ''
        ])
    
    return response

@login_required
def patient_print(request, patient_id):
    """Print patient information"""
    
    if not request.user.role in ['doctor', 'administrator', 'billing_staff']:
        messages.error(request, "You don't have permission to print patient data.")
        return redirect('patients:patient_list')
    
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    # Calculate age
    if patient.user.date_of_birth:
        today = date.today()
        age = today.year - patient.user.date_of_birth.year - ((today.month, today.day) < (patient.user.date_of_birth.month, patient.user.date_of_birth.day))
    else:
        age = None
    
    context = {
        'patient': patient,
        'age': age,
        'print_date': timezone.now(),
        'printed_by': request.user.get_full_name() or request.user.email,
    }
    
    return render(request, 'patient_print.html', context)