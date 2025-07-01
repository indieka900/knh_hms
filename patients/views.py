from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .forms import PatientCreationForm
from .models import Patient

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