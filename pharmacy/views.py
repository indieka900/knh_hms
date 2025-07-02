from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from django.db import models
import json

from .models import Pharmacist, Medicine, Inventory, MedicineDispensing
from .forms import PharmacistForm, MedicineForm, InventoryForm, DispensingForm, PatientSearchForm
from medical_records.models import Patient, Prescription


@login_required
def pharmacy_dashboard(request):
    """Main pharmacy dashboard view"""
    # Get dashboard statistics
    total_patients = Patient.objects.count()
    '''pending_prescriptions = Prescription.objects.filter(
        status='pending'
    ).count()'''
    
    # Get low stock items (quantity <= minimum_stock_level)
    low_stock_items = Inventory.objects.filter(
        quantity_in_stock__lte=models.F('minimum_stock_level')
    ).count()
    
    # Get today's dispensing count
    today = timezone.now().date()
    today_dispensed = MedicineDispensing.objects.filter(
        dispensed_at__date=today
    ).count()
    
    # Get recent patients
    recent_patients = Patient.objects.order_by('-created_at')[:5]
    
    # Get pending prescriptions
    '''pending_prescriptions_list = Prescription.objects.filter(
        status='pending'
    ).select_related('patient').order_by('-created_at')[:10]'''
    
    # Get inventory items with low stock or expiring soon
    critical_inventory = Inventory.objects.filter(
        Q(quantity_in_stock__lte=models.F('minimum_stock_level')) |
        Q(expiry_date__lte=date.today() + timedelta(days=90))
    ).select_related('medicine').order_by('quantity_in_stock')[:10]
    
    # Get recent dispensing history
    recent_dispensing = MedicineDispensing.objects.select_related(
        'prescription__patient', 'inventory_item__medicine', 'pharmacist'
    ).order_by('-dispensed_at')[:10]
    
    context = {
        'stats': {
            'total_patients': total_patients,
            # 'pending_prescriptions': pending_prescriptions,
            'low_stock_items': low_stock_items,
            'today_dispensed': today_dispensed,
        },
        'recent_patients': recent_patients,
        # 'pending_prescriptions_list': pending_prescriptions_list,
        'critical_inventory': critical_inventory,
        'recent_dispensing': recent_dispensing,
    }
    
    return render(request, 'pharmacy_dash.html', context)


@login_required
def patient_list_api(request):
    """API endpoint for patient list with search"""
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    patients = Patient.objects.all()
    
    if search_query:
        patients = patients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(patient_id__icontains=search_query)
        )
    
    patients = patients.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(patients, 10)
    patients_page = paginator.get_page(page)
    
    patients_data = []
    for patient in patients_page:
        patients_data.append({
            'id': patient.patient_id,
            'name': patient.get_full_name(),
            'phone': patient.phone_number,
            'email': patient.email,
            'age': patient.age if hasattr(patient, 'age') else '',
            'last_visit': patient.created_at.strftime('%Y-%m-%d'),
        })
    
    return JsonResponse({
        'patients': patients_data,
        'has_next': patients_page.has_next(),
        'has_previous': patients_page.has_previous(),
        'total': paginator.count
    })


@login_required
def prescription_list_api(request):
    """API endpoint for prescription list with search"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    prescriptions = Prescription.objects.select_related('patient').all()
    
    if search_query:
        prescriptions = prescriptions.filter(
            Q(prescription_id__icontains=search_query) |
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(doctor_name__icontains=search_query)
        )
    
    if status_filter:
        prescriptions = prescriptions.filter(status=status_filter)
    
    prescriptions = prescriptions.order_by('-created_at')
    
    prescriptions_data = []
    for prescription in prescriptions:
        # Get medicines from prescription items
        medicines = [item.medicine_name for item in prescription.prescription_items.all()]
        
        prescriptions_data.append({
            'id': prescription.prescription_id,
            'patient_id': prescription.patient.patient_id,
            'patient_name': prescription.patient.get_full_name(),
            'doctor': prescription.doctor_name,
            'date': prescription.created_at.strftime('%Y-%m-%d'),
            'medicines': medicines,
            'status': prescription.status,
        })
    
    return JsonResponse({
        'prescriptions': prescriptions_data
    })


@login_required
def inventory_list_api(request):
    """API endpoint for inventory list with search"""
    search_query = request.GET.get('search', '')
    
    inventory = Inventory.objects.select_related('medicine').all()
    
    if search_query:
        inventory = inventory.filter(
            Q(medicine__name__icontains=search_query) |
            Q(medicine__generic_name__icontains=search_query) |
            Q(batch_number__icontains=search_query) |
            Q(supplier__icontains=search_query)
        )
    
    inventory = inventory.order_by('medicine__name')
    
    inventory_data = []
    for item in inventory:
        # Determine status
        status = 'normal'
        if item.quantity_in_stock <= 5:
            status = 'critical'
        elif item.quantity_in_stock <= item.minimum_stock_level:
            status = 'low'
        
        # Check expiry
        months_to_expiry = (item.expiry_date - date.today()).days / 30
        if months_to_expiry < 3:
            status = 'expiring'
        
        inventory_data.append({
            'id': item.id,
            'medicine_name': f"{item.medicine.name} ({item.medicine.generic_name})",
            'batch_number': item.batch_number,
            'quantity': item.quantity_in_stock,
            'unit_price': float(item.unit_price),
            'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
            'supplier': item.supplier,
            'min_stock_level': item.minimum_stock_level,
            'status': status,
        })
    
    return JsonResponse({
        'inventory': inventory_data
    })


@login_required
def dispensing_history_api(request):
    """API endpoint for dispensing history"""
    dispensing_records = MedicineDispensing.objects.select_related(
        'prescription__patient', 'inventory_item__medicine', 'pharmacist__user'
    ).order_by('-dispensed_at')[:20]
    
    dispensing_data = []
    for record in dispensing_records:
        dispensing_data.append({
            'id': record.id,
            'prescription_id': record.prescription.prescription_id,
            'patient_name': record.prescription.patient.get_full_name(),
            'medicine_name': record.inventory_item.medicine.name,
            'quantity': record.quantity_dispensed,
            'dispensed_at': record.dispensed_at.strftime('%Y-%m-%d %H:%M'),
            'pharmacist': record.pharmacist.user.get_full_name(),
            'notes': record.notes,
        })
    
    return JsonResponse({
        'dispensing_history': dispensing_data
    })


@login_required
@require_http_methods(['POST'])
def add_patient_api(request):
    """API endpoint to add new patient"""
    try:
        data = json.loads(request.body)
        
        # Create patient
        patient = Patient.objects.create(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone_number=data.get('phone'),
            email=data.get('email', ''),
            date_of_birth=data.get('date_of_birth') if data.get('date_of_birth') else None,
            address=data.get('address', ''),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Patient added successfully',
            'patient': {
                'id': patient.patient_id,
                'name': patient.get_full_name(),
                'phone': patient.phone_number,
                'email': patient.email,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_http_methods(['POST'])
def add_medicine_api(request):
    """API endpoint to add medicine to inventory"""
    try:
        data = json.loads(request.body)
        
        # Get or create medicine
        medicine, created = Medicine.objects.get_or_create(
            name=data.get('medicine_name'),
            defaults={
                'generic_name': data.get('generic_name', ''),
                'manufacturer': data.get('manufacturer'),
                'unit_of_measurement': data.get('unit', 'tablets'),
            }
        )
        
        # Create inventory item
        inventory_item = Inventory.objects.create(
            medicine=medicine,
            batch_number=data.get('batch_number'),
            quantity_in_stock=int(data.get('quantity')),
            unit_price=float(data.get('unit_price')),
            expiry_date=data.get('expiry_date'),
            supplier=data.get('supplier'),
            minimum_stock_level=int(data.get('min_stock_level', 10)),
            date_received=date.today(),
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Medicine added to inventory successfully',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_http_methods(['POST'])
def dispense_medicine_api(request):
    """API endpoint to dispense medicine"""
    try:
        data = json.loads(request.body)
        
        # Get prescription
        prescription = get_object_or_404(
            Prescription, 
            prescription_id=data.get('prescription_id')
        )
        
        # Get inventory item
        inventory_item = get_object_or_404(
            Inventory, 
            id=data.get('inventory_item_id')
        )
        
        quantity_to_dispense = int(data.get('quantity'))
        
        # Check stock
        if inventory_item.quantity_in_stock < quantity_to_dispense:
            return JsonResponse({
                'success': False,
                'message': 'Insufficient stock available'
            }, status=400)
        
        # Get or create pharmacist record for current user
        pharmacist, created = Pharmacist.objects.get_or_create(
            user=request.user,
            defaults={
                'pharmacist_id': f'PH{request.user.id:04d}',
                'license_number': 'TEMP_LICENSE',
            }
        )
        
        # Create dispensing record
        dispensing = MedicineDispensing.objects.create(
            prescription=prescription,
            inventory_item=inventory_item,
            pharmacist=pharmacist,
            quantity_dispensed=quantity_to_dispense,
            notes=data.get('notes', ''),
        )
        
        # Update inventory
        inventory_item.quantity_in_stock -= quantity_to_dispense
        inventory_item.save()
        
        # Update prescription status
        prescription.status = 'dispensed'
        prescription.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Medicine dispensed successfully',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_http_methods(['POST'])
def update_stock_api(request):
    """API endpoint to update inventory stock"""
    try:
        data = json.loads(request.body)
        
        inventory_item = get_object_or_404(Inventory, id=data.get('item_id'))
        new_quantity = int(data.get('quantity'))
        
        inventory_item.quantity_in_stock = new_quantity
        inventory_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Stock updated successfully',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
def get_medicines_for_select_api(request):
    """API endpoint to get medicines for select dropdown"""
    inventory_items = Inventory.objects.filter(
        quantity_in_stock__gt=0
    ).select_related('medicine').order_by('medicine__name')
    
    medicines_data = []
    for item in inventory_items:
        medicines_data.append({
            'id': item.id,
            'name': f"{item.medicine.name} (Stock: {item.quantity_in_stock})",
            'stock': item.quantity_in_stock,
        })
    
    return JsonResponse({
        'medicines': medicines_data
    })


@login_required
def patient_detail_api(request, patient_id):
    """API endpoint for patient details"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    
    patient_data = {
        'id': patient.patient_id,
        'name': patient.get_full_name(),
        'phone': patient.phone_number,
        'email': patient.email,
        'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else '',
        'address': patient.address,
        'created_at': patient.created_at.strftime('%Y-%m-%d'),
    }
    
    return JsonResponse({
        'patient': patient_data
    })


@login_required
def inventory_detail_api(request, item_id):
    """API endpoint for inventory item details"""
    item = get_object_or_404(Inventory, id=item_id)
    
    item_data = {
        'id': item.id,
        'medicine_name': item.medicine.name,
        'generic_name': item.medicine.generic_name,
        'manufacturer': item.medicine.manufacturer,
        'batch_number': item.batch_number,
        'quantity': item.quantity_in_stock,
        'unit_price': float(item.unit_price),
        'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
        'supplier': item.supplier,
        'min_stock_level': item.minimum_stock_level,
        'date_received': item.date_received.strftime('%Y-%m-%d'),
    }
    
    return JsonResponse({
        'item': item_data
    })


# Traditional form-based views (if needed)
'''@login_required
def add_patient(request):
    """Traditional form view to add patient"""
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient added successfully!')
            return redirect('pharmacy:dashboard')
    else:
        form = PatientForm()
    
    return render(request, 'pharmacy/add_patient.html', {'form': form})'''


@login_required
def add_medicine(request):
    """Traditional form view to add medicine"""
    if request.method == 'POST':
        medicine_form = MedicineForm(request.POST)
        inventory_form = InventoryForm(request.POST)
        
        if medicine_form.is_valid() and inventory_form.is_valid():
            medicine = medicine_form.save()
            inventory = inventory_form.save(commit=False)
            inventory.medicine = medicine
            inventory.save()
            
            messages.success(request, 'Medicine added to inventory successfully!')
            return redirect('pharmacy:dashboard')
    else:
        medicine_form = MedicineForm()
        inventory_form = InventoryForm()
    
    context = {
        'medicine_form': medicine_form,
        'inventory_form': inventory_form,
    }
    return render(request, 'pharmacy/add_medicine.html', context)