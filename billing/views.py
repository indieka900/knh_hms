from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta, date
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from decimal import Decimal
import json
from django.views.decorators.http import require_http_methods

from .utils import generate_payment_id_uuid
from .models import Bill, BillItem, Payment, ServiceType, BillingStaff
from patients.models import Patient
from appointments.models import Appointment

@login_required
def billing_dashboard(request):
    """Billing dashboard with key metrics"""
    context = {
        'total_revenue_today': Payment.objects.filter(
            payment_date__date=timezone.now().date()
        ).aggregate(total=Sum('amount'))['total'] or 0,
        
        'pending_bills_count': Bill.objects.filter(status='pending').count(),
        'overdue_bills_count': Bill.objects.filter(
            status='overdue',
            due_date__lt=timezone.now().date()
        ).count(),
        
        'recent_payments': Payment.objects.select_related('bill__patient__user')
                                        .order_by('-payment_date')[:5],
        
        'pending_bills': Bill.objects.select_related('patient__user')
                                .filter(status='pending')
                                .order_by('-created_at')[:10],
        
        'revenue_this_month': Payment.objects.filter(
            payment_date__month=timezone.now().month,
            payment_date__year=timezone.now().year
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    return render(request, 'billing/dashboard.html', context)

@login_required
def bill_list(request):
    """List all bills with filtering options"""
    bills = Bill.objects.select_related('patient__user').order_by('-created_at')
    
    # Filtering
    status = request.GET.get('status')
    patient_search = request.GET.get('patient')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        bills = bills.filter(status=status)
    if patient_search:
        bills = bills.filter(
            Q(patient__user__first_name__icontains=patient_search) |
            Q(patient__user__last_name__icontains=patient_search) |
            Q(patient__patient_id__icontains=patient_search)
        )
    if date_from:
        bills = bills.filter(issue_date__gte=date_from)
    if date_to:
        bills = bills.filter(issue_date__lte=date_to)
    
    paginator = Paginator(bills, 20)
    page_number = request.GET.get('page')
    bills = paginator.get_page(page_number)
    
    context = {
        'bills': bills,
        'status_choices': Bill.BILL_STATUS,
        'current_filters': {
            'status': status,
            'patient': patient_search,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'billing/bill_list.html', context)

@login_required
def create_bill(request):
    """Create a new bill"""
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient_id')
            appointment_id = request.POST.get('appointment_id')
            due_date = request.POST.get('due_date')
            notes = request.POST.get('notes', '')
            
            patient = get_object_or_404(Patient, patient_id=patient_id)
            appointment = None
            if appointment_id:
                appointment = get_object_or_404(Appointment, id=appointment_id)
            
            # Generate bill ID
            bill_id = f"BILL{timezone.now().strftime('%Y%m%d')}{Bill.objects.count() + 1:04d}"
            
            # Get billing staff
            billing_staff = BillingStaff.objects.get(user=request.user)
            
            # Create bill
            bill = Bill.objects.create(
                bill_id=bill_id,
                patient=patient,
                appointment=appointment,
                due_date=due_date,
                created_by=billing_staff,
                notes=notes
            )
            
            # Process bill items
            services = request.POST.getlist('service[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            descriptions = request.POST.getlist('description[]')
            
            total_amount = Decimal('0')
            for i in range(len(services)):
                if services[i] and quantities[i] and unit_prices[i]:
                    service = get_object_or_404(ServiceType, id=services[i])
                    quantity = int(quantities[i])
                    unit_price = Decimal(unit_prices[i])
                    description = descriptions[i] if i < len(descriptions) else ''
                    
                    bill_item = BillItem.objects.create(
                        bill=bill,
                        service_type=service,
                        description=description or service.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=quantity * unit_price
                    )
                    total_amount += bill_item.total_price
            
            # Update bill total
            bill.total_amount = total_amount
            bill.save()
            
            messages.success(request, f'Bill {bill.bill_id} created successfully!')
            return redirect('billing:bill_detail', bill_id=bill.bill_id)
            
        except Exception as e:
            messages.error(request, f'Error creating bill: {str(e)}')
    
    # GET request - show form
    patients = Patient.objects.select_related('user').all()
    service_types = ServiceType.objects.filter(is_active=True)
    default_due_date = date.today().isoformat()
    
    context = {
        'patients': patients,
        'service_types': service_types,
        'default_due_date': default_due_date,
    }
    return render(request, 'billing/create_bill.html', context)

@login_required
def bill_detail(request, bill_id):
    """Display bill details"""
    bill = get_object_or_404(Bill, bill_id=bill_id)
    bill_items = BillItem.objects.filter(bill=bill).select_related('service_type')
    payments = Payment.objects.filter(bill=bill).order_by('-payment_date')
    
    context = {
        'bill': bill,
        'bill_items': bill_items,
        'payments': payments,
        'balance_due': bill.balance_due,
    }
    return render(request, 'billing/bill_detail.html', context)

@login_required
def process_payment(request, bill_id):
    """Process payment for a bill"""
    bill = get_object_or_404(Bill, bill_id=bill_id)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            payment_method = request.POST.get('payment_method')
            transaction_reference = request.POST.get('transaction_reference', '')
            notes = request.POST.get('notes', '')
            
            if amount <= 0:
                messages.error(request, 'Payment amount must be greater than zero.')
                return redirect('billing:bill_detail', bill_id=bill_id)
            
            if amount > bill.balance_due:
                messages.error(request, 'Payment amount cannot exceed the outstanding balance.')
                return redirect('billing:bill_detail', bill_id=bill_id)
            
            # Generate payment ID
            
            # Get billing staff
            billing_staff = BillingStaff.objects.get(user=request.user)
            
            # Create payment
            Payment.objects.create(
                payment_id = generate_payment_id_uuid(),
                bill=bill,
                amount=amount,
                payment_method=payment_method,
                transaction_reference=transaction_reference,
                processed_by=billing_staff,
                notes=notes
            )
            
            # Update bill status and amount paid
            bill.amount_paid += amount
            if bill.amount_paid >= bill.total_amount:
                bill.status = 'paid'
            elif bill.amount_paid > 0:
                bill.status = 'partial'
            bill.save()
            
            messages.success(request, f'Payment of KSh {amount:,.2f} processed successfully!')
            return redirect('billing:bill_detail', bill_id=bill_id)
            
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    context = {
        'bill': bill,
        'payment_methods': Payment.PAYMENT_METHODS,
    }
    return render(request, 'billing/process_payment.html', context)

@login_required
def get_patient_bills(request, patient_id):
    """API endpoint to get patient bills"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    bills = Bill.objects.filter(patient=patient).order_by('-created_at')
    
    bills_data = []
    for bill in bills:
        bills_data.append({
            'bill_id': bill.bill_id,
            'total_amount': float(bill.total_amount),
            'amount_paid': float(bill.amount_paid),
            'balance_due': float(bill.balance_due),
            'status': bill.get_status_display(),
            'issue_date': bill.issue_date.strftime('%Y-%m-%d'),
            'due_date': bill.due_date.strftime('%Y-%m-%d'),
        })
    
    return JsonResponse({'bills': bills_data})

@login_required
def edit_bill(request, bill_id):
    """Edit an existing bill"""
    bill = get_object_or_404(Bill, bill_id=bill_id)
    
    # Check if bill can be edited (only pending or partial bills)
    if bill.status in ['paid', 'cancelled']:
        messages.error(request, 'Cannot edit a paid or cancelled bill.')
        return redirect('billing:bill_detail', bill_id=bill_id)
    
    if request.method == 'POST':
        try:
            # Update bill details
            bill.due_date = request.POST.get('due_date')
            bill.notes = request.POST.get('notes', '')
            
            # Clear existing bill items
            BillItem.objects.filter(bill=bill).delete()
            
            # Process new bill items
            services = request.POST.getlist('service[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            descriptions = request.POST.getlist('description[]')
            
            total_amount = Decimal('0')
            for i in range(len(services)):
                if services[i] and quantities[i] and unit_prices[i]:
                    service = get_object_or_404(ServiceType, id=services[i])
                    quantity = int(quantities[i])
                    unit_price = Decimal(unit_prices[i])
                    description = descriptions[i] if i < len(descriptions) else ''
                    
                    bill_item = BillItem.objects.create(
                        bill=bill,
                        service_type=service,
                        description=description or service.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=quantity * unit_price
                    )
                    total_amount += bill_item.total_price
            
            # Update bill total
            bill.total_amount = total_amount
            bill.save()
            
            messages.success(request, f'Bill {bill.bill_id} updated successfully!')
            return redirect('billing:bill_detail', bill_id=bill.bill_id)
            
        except Exception as e:
            messages.error(request, f'Error updating bill: {str(e)}')
    
    # GET request - show form
    service_types = ServiceType.objects.filter(is_active=True)
    bill_items = BillItem.objects.filter(bill=bill).select_related('service_type')
    
    context = {
        'bill': bill,
        'service_types': service_types,
        'bill_items': bill_items,
    }
    return render(request, 'billing/edit_bill.html', context)

@login_required
def print_bill(request, bill_id):
    """Generate printable bill"""
    bill = get_object_or_404(Bill, bill_id=bill_id)
    bill_items = BillItem.objects.filter(bill=bill).select_related('service_type')
    payments = Payment.objects.filter(bill=bill).order_by('-payment_date')
    
    context = {
        'bill': bill,
        'bill_items': bill_items,
        'payments': payments,
        'print_date': timezone.now(),
    }
    return render(request, 'billing/print_bill.html', context)

@login_required
def payment_list(request):
    """List all payments with filtering"""
    payments = Payment.objects.select_related(
        'bill__patient__user', 'processed_by__user'
    ).order_by('-payment_date')
    
    # Filtering
    patient_search = request.GET.get('patient')
    payment_method = request.GET.get('payment_method')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if patient_search:
        payments = payments.filter(
            Q(bill__patient__user__first_name__icontains=patient_search) |
            Q(bill__patient__user__last_name__icontains=patient_search) |
            Q(bill__patient__patient_id__icontains=patient_search)
        )
    
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)
    
    paginator = Paginator(payments, 25)
    page_number = request.GET.get('page')
    payments = paginator.get_page(page_number)
    
    context = {
        'payments': payments,
        'payment_methods': Payment.PAYMENT_METHODS,
        'current_filters': {
            'patient': patient_search,
            'payment_method': payment_method,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'billing/payment_list.html', context)

@login_required
def payment_detail(request, payment_id):
    """Display payment details"""
    payment = get_object_or_404(Payment, payment_id=payment_id)
    
    context = {
        'payment': payment,
        'bill': payment.bill,
    }
    return render(request, 'billing/payment_detail.html', context)

@login_required
def service_type_list(request):
    """List all service types"""
    service_types = ServiceType.objects.all().order_by('name')
    
    # Filtering
    search = request.GET.get('search')
    status = request.GET.get('status')
    
    if search:
        service_types = service_types.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if status == 'active':
        service_types = service_types.filter(is_active=True)
    elif status == 'inactive':
        service_types = service_types.filter(is_active=False)
    
    paginator = Paginator(service_types, 20)
    page_number = request.GET.get('page')
    service_types = paginator.get_page(page_number)
    
    context = {
        'service_types': service_types,
        'current_filters': {
            'search': search,
            'status': status,
        }
    }
    return render(request, 'billing/service_type_list.html', context)

@login_required
def create_service_type(request):
    """Create a new service type"""
    if request.method == 'POST':
        try:
            ServiceType.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                base_price=Decimal(request.POST.get('base_price')),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            messages.success(request, 'Service type created successfully!')
            return redirect('billing:service_type_list')
            
        except Exception as e:
            messages.error(request, f'Error creating service type: {str(e)}')
    
    return render(request, 'billing/create_service_type.html')

@login_required
def edit_service_type(request, service_id):
    """Edit service type"""
    service_type = get_object_or_404(ServiceType, id=service_id)
    
    if request.method == 'POST':
        try:
            service_type.name = request.POST.get('name')
            service_type.description = request.POST.get('description', '')
            service_type.base_price = Decimal(request.POST.get('base_price'))
            service_type.is_active = request.POST.get('is_active') == 'on'
            service_type.save()
            
            messages.success(request, 'Service type updated successfully!')
            return redirect('billing:service_type_list')
            
        except Exception as e:
            messages.error(request, f'Error updating service type: {str(e)}')
    
    context = {
        'service_type': service_type,
    }
    return render(request, 'billing/edit_service_type.html', context)

@login_required
def billing_reports(request):
    """Billing reports dashboard"""
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    
    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Revenue statistics
    payments_in_range = Payment.objects.filter(
        payment_date__date__gte=date_from,
        payment_date__date__lte=date_to
    )
    
    total_revenue = payments_in_range.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Payment method breakdown
    payment_methods = payments_in_range.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('bill_id')
    ).order_by('-total')
    
    # Daily revenue for chart
    daily_revenue = payments_in_range.extra(
        select={'day': 'date(payment_date)'}
    ).values('day').annotate(
        total=Sum('amount')
    ).order_by('day')
    
    # Outstanding bills
    outstanding_bills = Bill.objects.exclude(status__in=['paid', 'cancelled'])
    total_outstanding = outstanding_bills.aggregate(
        total=Sum('total_amount') - Sum('amount_paid')
    )['total'] or 0
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_revenue': total_revenue,
        'payment_methods': payment_methods,
        'daily_revenue': list(daily_revenue),
        'total_outstanding': total_outstanding,
        'outstanding_bills_count': outstanding_bills.count(),
    }
    return render(request, 'billing/reports.html', context)

@login_required
def revenue_report(request):
    """Detailed revenue report"""
    # Similar to billing_reports but more detailed
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    
    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Detailed revenue breakdown
    payments = Payment.objects.filter(
        payment_date__date__gte=date_from,
        payment_date__date__lte=date_to
    ).select_related('bill__patient__user', 'processed_by__user')
    
    # Service-wise revenue
    service_revenue = BillItem.objects.filter(
        bill__created_at__date__gte=date_from,
        bill__created_at__date__lte=date_to
    ).values('service_type__name').annotate(
        total_revenue=Sum('total_price'),
        quantity_sold=Sum('quantity')
    ).order_by('-total_revenue')
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'payments': payments,
        'service_revenue': service_revenue,
    }
    return render(request, 'billing/revenue_report.html', context)

@login_required
def calculate_bill_total(request):
    """API endpoint to calculate bill total"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            total = Decimal('0')
            for item in items:
                quantity = Decimal(str(item.get('quantity', 0)))
                unit_price = Decimal(str(item.get('unit_price', 0)))
                total += quantity * unit_price
            
            return JsonResponse({
                'total': float(total),
                'formatted_total': f"KSh {total:,.2f}"
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@require_http_methods(["GET"])
def patient_pending_bills_api(request, patient_id):
    """API endpoint to get pending bills for a patient"""
    try:
        patient = get_object_or_404(Patient, patient_id=patient_id)
        
        # Get bills that have a balance (not fully paid)
        pending_bills = Bill.objects.filter(
            patient=patient,
            status__in=['pending', 'partial']  # Adjust status values as per your model
        ).annotate(
            paid_amount=Sum('payments__amount')  # Assuming you have a Payment model with reverse relation
        ).order_by('-created_at')
        
        bills_data = []
        for bill in pending_bills:
            paid_amount = bill.paid_amount or Decimal('0')
            balance = bill.total_amount - paid_amount
            
            # Only include bills with positive balance
            if balance > 0:
                bills_data.append({
                    'bill_id': bill.bill_id,
                    'total_amount': str(bill.total_amount),
                    'paid_amount': str(paid_amount),
                    'balance': str(balance),
                    'due_date': bill.due_date.strftime('%Y-%m-%d'),
                    'created_date': bill.created_at.strftime('%Y-%m-%d'),
                    'status': bill.status
                })
        
        return JsonResponse({
            'success': True,
            'bills': bills_data,
            'patient_name': f"{patient.user.first_name} {patient.user.last_name}",
            'patient_id': patient.patient_id
        })
        
    except Patient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Patient not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
@transaction.atomic 
def quick_payment_api(request):
    """API endpoint to process quick payments"""
    try:
        # Get form data
        patient_id = request.POST.get('patient_id')
        bill_id = request.POST.get('bill_id')
        amount_str = request.POST.get('amount', '0')
        payment_method = request.POST.get('payment_method')
        transaction_ref = request.POST.get('transaction_ref', '')
        
        # Validate and parse amount
        try:
            amount = Decimal(amount_str)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid amount format'
            }, status=400)
        
        # Validate required fields
        if not all([patient_id, bill_id, payment_method]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Payment amount must be greater than 0'
            }, status=400)
        
        # Get patient and bill
        try:
            patient = get_object_or_404(Patient, patient_id=patient_id)
            bill = get_object_or_404(Bill, bill_id=bill_id, patient=patient)
        except (Patient.DoesNotExist, Bill.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Patient or Bill not found'
            }, status=404)
        
        # Calculate current balance
        paid_amount = bill.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        current_balance = bill.total_amount - paid_amount
        
        # Validate payment amount against balance
        if amount > current_balance:
            return JsonResponse({
                'success': False,
                'error': f'Payment amount cannot exceed balance of KSh {current_balance:,.2f}'
            }, status=400)
        
        # Check if bill is already fully paid
        if current_balance <= 0:
            return JsonResponse({
                'success': False,
                'error': 'This bill is already fully paid'
            }, status=400)
        
        # Get billing staff
        try:
            billing_staff = get_object_or_404(BillingStaff, user=request.user)
        except BillingStaff.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User is not authorized to process payments'
            }, status=403)
        
        
        # Create payment record
        payment = Payment.objects.create(
            payment_id = generate_payment_id_uuid(),
            bill=bill,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=transaction_ref,
            processed_by=billing_staff,
            payment_date=timezone.now().date()
        )
        
        # Calculate new totals
        new_paid_amount = paid_amount + amount
        new_balance = bill.total_amount - new_paid_amount
        
        # Update bill status
        if new_balance <= 0:
            bill.status = 'paid'
        elif paid_amount == 0:
            bill.status = 'partial'
        else:
            bill.status = 'partial' 
        
        bill.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully',
            'payment_id': payment.payment_id,
            'payment_pk': payment.pk,
            'new_balance': str(new_balance),
            'payment_amount': str(amount),
            'bill_status': bill.status,
            'total_paid': str(new_paid_amount)
        })
        
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Quick payment error: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=500)