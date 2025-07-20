from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
import json

from .models import MedicalRecord, Prescription, LabTest
from patients.models import Patient, PatientVitals
from appointments.models import Doctor, Appointment

@login_required
def medical_records_dashboard(request):
    """Medical records dashboard"""
    context = {
        'total_records_today': MedicalRecord.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
        
        'pending_lab_tests': LabTest.objects.filter(status='pending').count(),
        'pending_prescriptions': Prescription.objects.filter(
            is_dispensed=False
        ).count(),
        
        'recent_records': MedicalRecord.objects.select_related(
            'patient__user', 'doctor__user'
        ).order_by('-created_at')[:10],
        
        'recent_lab_tests': LabTest.objects.select_related(
            'medical_record__patient__user'
        ).order_by('-test_date')[:5],
        
        'critical_vitals': PatientVitals.objects.select_related(
            'patient__user'
        ).filter(
            # Add conditions for critical vitals (high BP, fever, etc.)
            Q(blood_pressure_systolic__gt=140) |
            Q(temperature__gt=38.0)
        ).order_by('-recorded_at')[:5],
    }
    return render(request, 'medical_records/dashboard.html', context)

@login_required
def medical_record_list(request):
    """List all medical records"""
    records = MedicalRecord.objects.select_related(
        'patient__user', 'doctor__user'
    ).order_by('-created_at')
    
    # Filtering
    patient_search = request.GET.get('patient')
    doctor_search = request.GET.get('doctor')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if patient_search:
        records = records.filter(
            Q(patient__user__first_name__icontains=patient_search) |
            Q(patient__user__last_name__icontains=patient_search) |
            Q(patient__patient_id__icontains=patient_search)
        )
    if doctor_search:
        records = records.filter(
            Q(doctor__user__first_name__icontains=doctor_search) |
            Q(doctor__user__last_name__icontains=doctor_search)
        )
    if date_from:
        records = records.filter(created_at__date__gte=date_from)
    if date_to:
        records = records.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    records = paginator.get_page(page_number)
    
    context = {
        'records': records,
        'current_filters': {
            'patient': patient_search,
            'doctor': doctor_search,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'medical_records/record_list.html', context)

@login_required
def create_medical_record(request, patient_id):
    """Create a new medical record"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            diagnosis = request.POST.get('diagnosis')
            symptoms = request.POST.get('symptoms')
            treatment_plan = request.POST.get('treatment_plan')
            notes = request.POST.get('notes', '')
            follow_up_date = request.POST.get('follow_up_date')
            appointment_id = request.POST.get('appointment_id')
            
            # Get doctor
            doctor = Doctor.objects.get(user=request.user)
            
            # Generate record ID
            record_id = f"MR{timezone.now().strftime('%Y%m%d')}{MedicalRecord.objects.count() + 1:04d}"
            
            # Get appointment if provided
            appointment = None
            if appointment_id:
                appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
            
            # Create medical record
            record = MedicalRecord.objects.create(
                record_id=record_id,
                patient=patient,
                doctor=doctor,
                appointment=appointment,
                diagnosis=diagnosis,
                symptoms=symptoms,
                treatment_plan=treatment_plan,
                notes=notes,
                follow_up_date=follow_up_date if follow_up_date else None
            )
            
            messages.success(request, f'Medical record {record.record_id} created successfully!')
            return redirect('medical_records:medical_record_detail', record_id=record.record_id)
            
        except Exception as e:
            messages.error(request, f'Error creating medical record: {str(e)}')
    
    # GET request - show form
    recent_appointments = Appointment.objects.filter(
        patient=patient,
        status__in=['scheduled', 'confirmed', 'in_progress']
    ).order_by('-appointment_date')[:5]
    
    # Get patient's recent vitals
    recent_vitals = PatientVitals.objects.filter(
        patient=patient
    ).order_by('-recorded_at').first()
    
    context = {
        'patient': patient,
        'recent_appointments': recent_appointments,
        'recent_vitals': recent_vitals,
    }
    return render(request, 'medical_records/create_record.html', context)

@login_required
def medical_record_detail(request, record_id):
    """Display medical record details"""
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    prescriptions = Prescription.objects.filter(medical_record=record)
    lab_tests = LabTest.objects.filter(medical_record=record)
    
    context = {
        'record': record,
        'prescriptions': prescriptions,
        'lab_tests': lab_tests,
    }
    return render(request, 'medical_records/record_detail.html', context)

@login_required
def patient_medical_history(request, patient_id):
    """Display complete medical history for a patient"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    # Get all medical records
    medical_records = MedicalRecord.objects.filter(
        patient=patient
    ).order_by('-created_at')
    
    # Get all prescriptions
    prescriptions = Prescription.objects.filter(
        medical_record__patient=patient
    ).order_by('-medical_record__created_at')
    
    # Get all lab tests
    lab_tests = LabTest.objects.filter(
        medical_record__patient=patient
    ).order_by('-test_date')
    
    # Get vitals history
    vitals = PatientVitals.objects.filter(
        patient=patient
    ).order_by('-recorded_at')[:10]
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'prescriptions': prescriptions,
        'lab_tests': lab_tests,
        'vitals': vitals,
    }
    return render(request, 'medical_records/patient_history.html', context)

@login_required
def create_prescription(request, record_id):
    """Create prescription for a medical record"""
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    
    if request.method == 'POST':
        try:
            medications = request.POST.getlist('medication_name[]')
            dosages = request.POST.getlist('dosage[]')
            frequencies = request.POST.getlist('frequency[]')
            durations = request.POST.getlist('duration[]')
            instructions_list = request.POST.getlist('instructions[]')
            
            for i in range(len(medications)):
                if medications[i]:  # Only create if medication name is provided
                    Prescription.objects.create(
                        medical_record=record,
                        medication_name=medications[i],
                        dosage=dosages[i] if i < len(dosages) else '',
                        frequency=frequencies[i] if i < len(frequencies) else '',
                        duration=durations[i] if i < len(durations) else '',
                        instructions=instructions_list[i] if i < len(instructions_list) else ''
                    )
            
            messages.success(request, 'Prescriptions created successfully!')
            return redirect('medical_records:medical_record_detail', record_id=record.record_id)
            
        except Exception as e:
            messages.error(request, f'Error creating prescriptions: {str(e)}')
    
    context = {
        'record': record,
    }
    return render(request, 'medical_records/create_prescription.html', context)

@login_required
def record_vitals(request, patient_id):
    """Record patient vitals"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    if request.method == 'POST':
        try:
            PatientVitals.objects.create(
                patient=patient,
                recorded_by=request.user,
                height=request.POST.get('height') or None,
                weight=request.POST.get('weight') or None,
                blood_pressure_systolic=request.POST.get('bp_systolic') or None,
                blood_pressure_diastolic=request.POST.get('bp_diastolic') or None,
                pulse_rate=request.POST.get('pulse_rate') or None,
                temperature=request.POST.get('temperature') or None,
            )
            
            messages.success(request, 'Vitals recorded successfully!')
            return redirect('medical_records:patient_medical_history', patient_id=patient_id)
            
        except Exception as e:
            messages.error(request, f'Error recording vitals: {str(e)}')
    
    # Get recent vitals for reference
    recent_vitals = PatientVitals.objects.filter(
        patient=patient
    ).order_by('-recorded_at').first()
    
    context = {
        'patient': patient,
        'recent_vitals': recent_vitals,
    }
    return render(request, 'medical_records/record_vitals.html', context)

@login_required
def patient_search(request):
    """API endpoint for patient search"""
    query = request.GET.get('q', '')
    if query:
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(patient_id__icontains=query)
        ).select_related('user')[:10]
        
        results = []
        for patient in patients:
            results.append({
                'id': patient.patient_id,
                'name': patient.user.get_full_name(),
                'patient_id': patient.patient_id,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

@login_required
def prescription_list(request):
    """List all prescriptions with filtering"""
    prescriptions = Prescription.objects.select_related(
        'medical_record__patient__user', 
        'medical_record__doctor__user'
    ).order_by('-medical_record__created_at')
    
    # Filtering
    patient_search = request.GET.get('patient')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if patient_search:
        prescriptions = prescriptions.filter(
            Q(medical_record__patient__user__first_name__icontains=patient_search) |
            Q(medical_record__patient__user__last_name__icontains=patient_search) |
            Q(medical_record__patient__patient_id__icontains=patient_search)
        )
    
    if status == 'dispensed':
        prescriptions = prescriptions.filter(is_dispensed=True)
    elif status == 'pending':
        prescriptions = prescriptions.filter(is_dispensed=False)
    
    if date_from:
        prescriptions = prescriptions.filter(medical_record__created_at__date__gte=date_from)
    if date_to:
        prescriptions = prescriptions.filter(medical_record__created_at__date__lte=date_to)
    
    paginator = Paginator(prescriptions, 25)
    page_number = request.GET.get('page')
    prescriptions = paginator.get_page(page_number)
    
    context = {
        'prescriptions': prescriptions,
        'current_filters': {
            'patient': patient_search,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'medical_records/prescription_list.html', context)

@login_required
def edit_medical_record(request, record_id):
    """Edit an existing medical record"""
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    
    # Check if user has permission to edit (doctor who created it or admin)
    if request.user.role not in ['admin'] and record.doctor.user != request.user:
        messages.error(request, 'You do not have permission to edit this record.')
        return redirect('medical_records:medical_record_detail', record_id=record_id)
    
    if request.method == 'POST':
        try:
            record.diagnosis = request.POST.get('diagnosis')
            record.symptoms = request.POST.get('symptoms')
            record.treatment_plan = request.POST.get('treatment_plan')
            record.notes = request.POST.get('notes', '')
            
            follow_up_date = request.POST.get('follow_up_date')
            record.follow_up_date = follow_up_date if follow_up_date else None
            
            record.save()
            
            messages.success(request, f'Medical record {record.record_id} updated successfully!')
            return redirect('medical_records:medical_record_detail', record_id=record.record_id)
            
        except Exception as e:
            messages.error(request, f'Error updating medical record: {str(e)}')
    
    context = {
        'record': record,
        'patient': record.patient,
    }
    return render(request, 'medical_records/edit_record.html', context)

@login_required
def print_medical_record(request, record_id):
    """Generate printable medical record"""
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    prescriptions = Prescription.objects.filter(medical_record=record)
    lab_tests = LabTest.objects.filter(medical_record=record)
    
    context = {
        'record': record,
        'prescriptions': prescriptions,
        'lab_tests': lab_tests,
        'print_date': timezone.now(),
    }
    return render(request, 'medical_records/print_record.html', context)

@login_required
def prescription_detail(request, prescription_id):
    """Display prescription details"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    context = {
        'prescription': prescription,
        'medical_record': prescription.medical_record,
        'patient': prescription.medical_record.patient,
    }
    return render(request, 'medical_records/prescription_detail.html', context)

@login_required
def edit_prescription(request, prescription_id):
    """Edit prescription"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    # Check permissions
    if request.user.role not in ['admin', 'pharmacist'] and prescription.medical_record.doctor.user != request.user:
        messages.error(request, 'You do not have permission to edit this prescription.')
        return redirect('medical_records:prescription_detail', prescription_id=prescription_id)
    
    if request.method == 'POST':
        try:
            prescription.medication_name = request.POST.get('medication_name')
            prescription.dosage = request.POST.get('dosage')
            prescription.frequency = request.POST.get('frequency')
            prescription.duration = request.POST.get('duration')
            prescription.instructions = request.POST.get('instructions', '')
            
            # Handle dispensing
            if request.POST.get('mark_dispensed') and not prescription.is_dispensed:
                prescription.is_dispensed = True
                prescription.dispensed_at = timezone.now()
                prescription.dispensed_by = request.user
            
            prescription.save()
            
            messages.success(request, 'Prescription updated successfully!')
            return redirect('medical_records:prescription_detail', prescription_id=prescription_id)
            
        except Exception as e:
            messages.error(request, f'Error updating prescription: {str(e)}')
    
    context = {
        'prescription': prescription,
    }
    return render(request, 'medical_records/edit_prescription.html', context)

@login_required
def lab_test_list(request):
    """List all lab tests"""
    lab_tests = LabTest.objects.select_related(
        'medical_record__patient__user'
    ).order_by('-test_date')
    
    # Filtering
    patient_search = request.GET.get('patient')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if patient_search:
        lab_tests = lab_tests.filter(
            Q(medical_record__patient__user__first_name__icontains=patient_search) |
            Q(medical_record__patient__user__last_name__icontains=patient_search) |
            Q(medical_record__patient__patient_id__icontains=patient_search)
        )
    
    if status:
        lab_tests = lab_tests.filter(status=status)
    
    if date_from:
        lab_tests = lab_tests.filter(test_date__date__gte=date_from)
    if date_to:
        lab_tests = lab_tests.filter(test_date__date__lte=date_to)
    
    paginator = Paginator(lab_tests, 25)
    page_number = request.GET.get('page')
    lab_tests = paginator.get_page(page_number)
    
    context = {
        'lab_tests': lab_tests,
        'status_choices': LabTest.TEST_STATUS,
        'current_filters': {
            'patient': patient_search,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'medical_records/lab_test_list.html', context)

@login_required
def create_lab_test(request, record_id):
    """Create lab tests for a medical record"""
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    
    if request.method == 'POST':
        try:
            test_names = request.POST.getlist('test_name[]')
            test_descriptions = request.POST.getlist('test_description[]')
            priorities = request.POST.getlist('priority[]')
            
            created_tests = []
            for i in range(len(test_names)):
                if test_names[i]:  # Only create if test name is provided
                    lab_test = LabTest.objects.create(
                        medical_record=record,
                        test_name=test_names[i],
                        test_description=test_descriptions[i] if i < len(test_descriptions) else '',
                        test_date=timezone.now(),
                    )
                    created_tests.append(lab_test)
            
            messages.success(request, f'{len(created_tests)} lab test(s) created successfully!')
            return redirect('medical_records:medical_record_detail', record_id=record.record_id)
            
        except Exception as e:
            messages.error(request, f'Error creating lab tests: {str(e)}')
    
    context = {
        'record': record,
    }
    return render(request, 'medical_records/create_lab_test.html', context)

@login_required
def lab_test_detail(request, test_id):
    """Display lab test details"""
    lab_test = get_object_or_404(LabTest, id=test_id)
    
    context = {
        'lab_test': lab_test,
        'medical_record': lab_test.medical_record,
        'patient': lab_test.medical_record.patient,
    }
    return render(request, 'medical_records/lab_test_detail.html', context)

@login_required
def edit_lab_test(request, test_id):
    """Edit lab test"""
    lab_test = get_object_or_404(LabTest, id=test_id)
    
    if request.method == 'POST':
        try:
            lab_test.test_name = request.POST.get('test_name')
            lab_test.test_description = request.POST.get('test_description')
            lab_test.status = request.POST.get('status')
            
            lab_test.save()
            
            messages.success(request, 'Lab test updated successfully!')
            return redirect('medical_records:lab_test_detail', test_id=test_id)
            
        except Exception as e:
            messages.error(request, f'Error updating lab test: {str(e)}')
    
    context = {
        'lab_test': lab_test,
        'status_choices': LabTest.TEST_STATUS,
    }
    return render(request, 'medical_records/edit_lab_test.html', context)

@login_required
def update_lab_results(request, test_id):
    """Update lab test results"""
    lab_test = get_object_or_404(LabTest, id=test_id)
    
    if request.method == 'POST':
        try:
            lab_test.results = request.POST.get('results')
            lab_test.status = 'completed'
            lab_test.result_date = timezone.now()
            
            lab_test.save()
            
            messages.success(request, 'Lab test results updated successfully!')
            return redirect('medical_records:lab_test_detail', test_id=test_id)
            
        except Exception as e:
            messages.error(request, f'Error updating results: {str(e)}')
    
    context = {
        'lab_test': lab_test,
    }
    return render(request, 'medical_records/update_lab_results.html', context)

@login_required
def vitals_history(request, patient_id):
    """Display patient vitals history"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    vitals = PatientVitals.objects.filter(
        patient=patient
    ).order_by('-recorded_at')
    
    paginator = Paginator(vitals, 20)
    page_number = request.GET.get('page')
    vitals = paginator.get_page(page_number)
    
    context = {
        'patient': patient,
        'vitals': vitals,
    }
    return render(request, 'medical_records/vitals_history.html', context)

@login_required
def get_medical_history(request, patient_id):
    """API endpoint to get patient medical history"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    records = MedicalRecord.objects.filter(
        patient=patient
    ).select_related('doctor__user').order_by('-created_at')[:10]
    
    history_data = []
    for record in records:
        history_data.append({
            'record_id': record.record_id,
            'diagnosis': record.diagnosis,
            'symptoms': record.symptoms,
            'treatment_plan': record.treatment_plan,
            'doctor_name': record.doctor.user.get_full_name(),
            'created_at': record.created_at.isoformat(),
        })
    
    return JsonResponse({'history': history_data})

@login_required
def get_prescription_template(request):
    """API endpoint to get prescription templates"""
    template_type = request.GET.get('type', 'common_cold')
    
    templates = {
        'common_cold': [
            {
                'medication_name': 'Paracetamol',
                'dosage': '500mg',
                'frequency': 'Three times daily',
                'duration': '5 days',
                'instructions': 'Take with food'
            },
            {
                'medication_name': 'Vitamin C',
                'dosage': '1000mg',
                'frequency': 'Once daily',
                'duration': '7 days',
                'instructions': 'Take with water'
            }
        ],
        'hypertension': [
            {
                'medication_name': 'Amlodipine',
                'dosage': '5mg',
                'frequency': 'Once daily',
                'duration': '30 days',
                'instructions': 'Take in the morning'
            },
            {
                'medication_name': 'Hydrochlorothiazide',
                'dosage': '25mg',
                'frequency': 'Once daily',
                'duration': '30 days',
                'instructions': 'Take with breakfast'
            }
        ],
        'diabetes': [
            {
                'medication_name': 'Metformin',
                'dosage': '500mg',
                'frequency': 'Twice daily',
                'duration': '30 days',
                'instructions': 'Take with meals'
            }
        ]
    }
    
    return JsonResponse({
        'template': templates.get(template_type, [])
    })