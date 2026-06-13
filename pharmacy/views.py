from datetime import date, timedelta, datetime
from decimal import Decimal
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from collections import defaultdict
from django.views import View
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from .models import Pharmacist, Medicine, Inventory, MedicineDispensing
from .forms import PharmacistForm, MedicineForm, InventoryForm, DispensingForm, PatientSearchForm
from medical_records.models import Patient, Prescription


@login_required
def pharmacy_dashboard(request):
    today = timezone.now().date()
    
    context = {
        'stats': {
            'total_patients': Patient.objects.count(),
            'low_stock_items': Inventory.objects.filter(quantity_in_stock__lte=F('minimum_stock_level')).count(),
            'today_dispensed': MedicineDispensing.objects.filter(dispensed_at__date=today).count(),
        },
        'recent_patients': Patient.objects.order_by('-created_at')[:5],
        'critical_inventory': Inventory.objects.filter(
            Q(quantity_in_stock__lte=F('minimum_stock_level')) |
            Q(expiry_date__lte=date.today() + timedelta(days=90))
        ).select_related('medicine').order_by('quantity_in_stock')[:10],
        'recent_dispensing': MedicineDispensing.objects.select_related(
            'prescription__patient', 'inventory_item__medicine', 'pharmacist'
        ).order_by('-dispensed_at')[:10],
    }
    return render(request, 'pharmacy_dash.html', context)


@login_required
def pharmacy_dashboard_data(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    today = timezone.now().date()
    
    critical_inventory = Inventory.objects.filter(
            Q(quantity_in_stock__lte=F('minimum_stock_level')) |
            Q(expiry_date__lte=date.today() + timedelta(days=90))
        ).select_related('medicine').order_by('quantity_in_stock')[:10]
    recent_dispensing = MedicineDispensing.objects.select_related(
            'prescription__medical_record__patient', 'inventory_item__medicine', 'pharmacist'
        ).order_by('-dispensed_at')[:10]

    data = {
        'stats': {
            'total_patients': Patient.objects.count(),
            'pending_prescriptions': Prescription.objects.filter(is_dispensed=False).count(),
            'low_stock_items': Inventory.objects.filter(quantity_in_stock__lte=F('minimum_stock_level')).count(),
            'today_dispensed': MedicineDispensing.objects.filter(dispensed_at__date=today).count(),
        },
        'recent_patients': [
            {
                'patient_id': p.patient_id,
                'first_name': p.user.first_name,
                'last_name': p.user.last_name,
                'phone_number': p.user.phone_number,
                'email': p.user.email,
                'age': 0,
                'address': "address",
                'created_at': p.created_at.isoformat() if p.created_at else None,
            }
            for p in Patient.objects.order_by('-created_at')[:5]
            
        ],
        'critical_inventory': [
            {
                'id': item.id,
                'medicine': {
                    'id': item.medicine.id,
                    'name': item.medicine.name,
                    'strength': getattr(item.medicine, 'strength', ''),
                },
                'batch_number': item.batch_number,
                'quantity_in_stock': item.quantity_in_stock,
                'unit_price': str(item.unit_price),
                'expiry_date': item.expiry_date.isoformat(),
                'supplier': item.supplier,
                'minimum_stock_level': item.minimum_stock_level,
                'date_received': item.date_received.isoformat() if item.date_received else None,
            }
            for item in critical_inventory
        ],
        'recent_dispensing': [
            {
                'id': record.id,
                'prescription_id': record.prescription.id if record.prescription else None,
                'prescription': {
                    'patient': {
                        'first_name': record.prescription.medical_record.patient.user.first_name,
                        'last_name': record.prescription.medical_record.patient.user.last_name,
                    }
                } if record.prescription else None,
                'inventory_item': {
                    'medicine': {
                        'name': record.inventory_item.medicine.name,
                        'strength': getattr(record.inventory_item.medicine, 'strength', '')
                    }
                },
                'quantity_dispensed': record.quantity_dispensed,
                'dispensed_at': record.dispensed_at.isoformat(),
                'pharmacist': {
                    'first_name': record.pharmacist.user.first_name,
                    'last_name': record.pharmacist.user.last_name,
                } if record.pharmacist else None,
                'notes': record.notes,
            }
            for record in recent_dispensing
        ]
    }

    return JsonResponse(data)



@login_required
@require_http_methods(["GET", "POST"])
def patients_api(request):
    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        patients = Patient.objects.all()

        if search_query:
            patients = patients.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(phone_number__icontains=search_query) |
                Q(patient_id__icontains=search_query)
            )

        patients = patients.order_by('-created_at')

        data = [{
            'patient_id': p.patient_id,
            'first_name': p.user.first_name,
            'last_name': p.user.last_name,
            'phone_number': p.user.phone_number,
            'email': p.user.email,
            # 'age': p.age,
            # 'address': p.address,
            'created_at': p.created_at.isoformat() if p.created_at else None,
        } for p in patients]

        return JsonResponse(data, safe=False)

    # POST
    try:
        data = json.loads(request.body)
        last_patient = Patient.objects.order_by('-id').first()
        last_num = int(last_patient.patient_id[1:]) if last_patient and last_patient.patient_id[1:].isdigit() else 0
        new_patient_id = f'P{str(last_num + 1).zfill(3)}'

        patient = Patient.objects.create(
            patient_id=new_patient_id,
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone_number'],
            email=data['email'],
            age=data['age'],
            address=data['address']
        )

        return JsonResponse({
            'patient_id': patient.patient_id,
            'first_name': patient.user.first_name,
            'last_name': patient.last_name,
            'phone_number': patient.phone_number,
            'email': patient.email,
            'age': patient.age,
            'address': patient.address,
            'created_at': patient.created_at.isoformat(),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["GET", "POST"])
def inventory_api(request):
    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        inventory = Inventory.objects.select_related('medicine').all()
        if search_query:
            inventory = inventory.filter(
                Q(medicine__name__icontains=search_query) |
                Q(batch_number__icontains=search_query) |
                Q(supplier__icontains=search_query)
            )
        inventory = inventory.order_by('quantity_in_stock')
        data = [{
            'id': item.id,
            'medicine': {
                'id': item.medicine.id,
                'name': item.medicine.name,
                'generic_name': item.medicine.generic_name,
            },
            'batch_number': item.batch_number,
            'quantity_in_stock': item.quantity_in_stock,
            'unit_price': str(item.unit_price),
            'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
            'supplier': item.supplier,
            'minimum_stock_level': item.minimum_stock_level,
            'date_received': item.date_received.isoformat() if item.date_received else None,
        } for item in inventory]
        return JsonResponse(data, safe=False)
    
    # Handle POST request
    try:
        data = json.loads(request.body)
        print(f"Received data: {data}")
        
        # Create or get the medicine
        medicine, created = Medicine.objects.get_or_create(
            name=data['medicine_name'],
            defaults={
                'generic_name': data.get('generic_name', ''),
                'manufacturer': data.get('manufacturer', ''),
                'unit_of_measurement': 'units',  # Add default unit
                'description': '',  # Add default description
            }
        )
        
        # Create the inventory item
        inventory_item = Inventory.objects.create(
            medicine=medicine,
            batch_number=data['batch_number'],
            quantity_in_stock=data['quantity_in_stock'],
            unit_price=Decimal(data['unit_price']),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date(),
            supplier=data['supplier'],
            minimum_stock_level=data['minimum_stock_level'],
            date_received=timezone.now().date()
        )
        
        return JsonResponse({
            'success': True,
            'id': inventory_item.id,
            'medicine': {
                'id': medicine.id,
                'name': medicine.name,
                'generic_name': medicine.generic_name,
            },
            'batch_number': inventory_item.batch_number,
            'quantity_in_stock': inventory_item.quantity_in_stock,
            'unit_price': str(inventory_item.unit_price),
            'expiry_date': inventory_item.expiry_date.isoformat() if inventory_item.expiry_date else None,
            'supplier': inventory_item.supplier,
            'minimum_stock_level': inventory_item.minimum_stock_level,
            'date_received': inventory_item.date_received.isoformat() if inventory_item.date_received else None,
        })
        
    except Exception as e:
        print(f"Error creating inventory item: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["PATCH"])
def update_stock_api(request, item_id):
    try:
        inventory_item = Inventory.objects.get(id=item_id)
        data = json.loads(request.body)
        inventory_item.quantity_in_stock = data['quantity_in_stock']
        inventory_item.save()

        return JsonResponse({
            'id': inventory_item.id,
            'quantity_in_stock': inventory_item.quantity_in_stock,
            'message': 'Stock updated successfully'
        })

    except Inventory.DoesNotExist:
        return JsonResponse({'error': 'Inventory item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



@login_required
@require_http_methods(["POST"])
def dispensing_api(request):
    try:
        data = json.loads(request.body)
        # print(f"Received dispensing data: {data}")
        inventory_item = Inventory.objects.get(id=data['inventory_item_id'])

        if inventory_item.quantity_in_stock < data['quantity_dispensed']:
            return JsonResponse({'error': 'Insufficient stock available'}, status=400)

        prescription = None
        if data.get('prescription_id'):
            prescription = Prescription.objects.get(id=1)
            pass
        pharmacist = Pharmacist.objects.get(user=request.user)
        dispensing = MedicineDispensing.objects.create(
            prescription=prescription,
            inventory_item=inventory_item,
            quantity_dispensed=data['quantity_dispensed'],
            pharmacist=pharmacist,
            notes=data.get('notes', ''),
            dispensed_at=timezone.now()
        )

        inventory_item.quantity_in_stock -= data['quantity_dispensed']
        inventory_item.save()

        return JsonResponse({
            'id': dispensing.id,
            'message': 'Medicine dispensed successfully',
            'remaining_stock': inventory_item.quantity_in_stock
        })

    except Inventory.DoesNotExist:
        return JsonResponse({'error': 'Inventory item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



def prescription_list_api(request):
    """API endpoint for prescription list grouped by medical record"""
    
    prescriptions = Prescription.objects.select_related(
        'medical_record__patient__user',
        'medical_record__doctor__user',
        'dispensed_by'
    ).all()
    # Group prescriptions by medical record
    grouped_prescriptions = defaultdict(list)
    for prescription in prescriptions:
        grouped_prescriptions[prescription.medical_record.record_id].append(prescription)
    prescriptions_data = []
    for record_id, prescription_list in grouped_prescriptions.items():
        # Use the first prescription to get patient/doctor info
        first_prescription = prescription_list[0]
        
        # Collect all medicines for this medical record
        medicines = [p.medication_name for p in prescription_list]
        
        # Determine overall status
        all_dispensed = all(p.is_dispensed for p in prescription_list)
        status = "dispensed" if all_dispensed else "pending"
        prescriptions_data.append({
            'id': record_id,
            'patient_id': first_prescription.medical_record.patient.patient_id,
            'patient_name': first_prescription.medical_record.patient.user.get_full_name(),
            'doctor': first_prescription.medical_record.doctor.user.get_full_name(),
            'date': first_prescription.medical_record.created_at.strftime('%Y-%m-%d'),
            'medicines': medicines,
            'status': status,
            'prescription_count': len(prescription_list)
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
