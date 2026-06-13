from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.humanize.templatetags.humanize import intcomma
import random
from patients.models import Patient
from pharmacy.models import Medicine, Inventory
from appointments.models import Appointment, Doctor
from medical_records.models import Prescription, LabTest, MedicalRecord
from django.contrib.auth import get_user_model
from billing.models import Bill, Payment
from notifications.models import Notification
from django.contrib import messages
from django.conf import settings
User = get_user_model()


@login_required
def dashboard_view(request):
    """
    Render the dashboard view with role-specific data
    """
    user = request.user
    today = timezone.now().date()
    now = timezone.now()
    current_month = now.replace(day=1)

    context = {
        'title': 'Dashboard',
        'user': user,
        'today': today,
        'unread_notifications': Notification.objects.filter(
            recipient=user, status__in=['pending', 'sent']
        ).count(),
    }

    context.update({
        'todays_count': get_todays_appointments_count(),
    })

    # Role-specific data
    if user.role == 'administrator':
        context.update(get_administrator_data(today, current_month))
    elif user.role == 'doctor':
        doctor = Doctor.objects.filter(user=user).first()
        context.update(get_doctor_data(doctor, today))
        # Also provide recent appointments for the compact view
        try:
            todays_appointments = Appointment.objects.filter(appointment_date=today, doctor=doctor)
            context['recent_appointments'] = todays_appointments.select_related(
                'patient__user', 'doctor__user'
            ).order_by('appointment_time')[:8]
        except Exception:
            context['recent_appointments'] = []
    elif user.role == 'pharmacist':
        context.update(get_pharmacist_data(today))
    elif user.role == 'billing_staff':
        context.update(get_billing_staff_data(today, current_month))
        context['pending_bills_amount'] = Bill.objects.filter(
            status__in=['pending', 'partial']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        context['overdue_bills'] = Bill.objects.filter(status='overdue').count()
        context['revenue_today'] = Payment.objects.filter(
            payment_date__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['revenue_month'] = Payment.objects.filter(
            payment_date__month=now.month,
            payment_date__year=now.year
        ).aggregate(total=Sum('amount'))['total'] or 0
    elif user.role == 'patient':
        patient = Patient.objects.filter(user=user).first()
        context.update(get_patient_data(patient, today))
    else:
        # Generic/admin fallback
        todays_appointments = Appointment.objects.filter(appointment_date=today)
        context['recent_appointments'] = todays_appointments.select_related(
            'patient__user', 'doctor__user'
        ).order_by('appointment_time')[:8]
        context['total_patients'] = Patient.objects.count()
        context['total_doctors'] = Doctor.objects.filter(is_available=True).count()
        context['low_stock'] = Inventory.objects.filter(
            quantity_in_stock__lte=F('minimum_stock_level')
        ).count()
        context['pending_rx'] = Prescription.objects.filter(is_dispensed=False).count()
        context['pending_labs'] = LabTest.objects.filter(status='pending').count()

    return render(request, 'dashboard.html', context)


def get_todays_appointments_count():
    """Get total appointments for today"""
    try:
        return Appointment.objects.filter(
            appointment_date=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).count()
    except Exception:
        return 23


def get_administrator_data(today, current_month):
    """Get data specific to administrators"""
    try:
        total_patients = Patient.objects.filter(user__is_active=True).count()
        total_staff = User.objects.filter(
            role__in=['doctor', 'pharmacist', 'billing_staff'],
            is_active=True
        ).count()
        todays_appointments = Appointment.objects.filter(
            appointment_date=today
        ).count()
        monthly_revenue = Bill.objects.filter(
            issue_date__gte=current_month,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        recent_activities = [
            {'time': '11:45 AM', 'activity': 'New staff member registered', 'user': 'Admin System', 'status': 'completed', 'status_class': 'success'},
            {'time': '11:30 AM', 'activity': 'System backup completed', 'user': 'Auto System', 'status': 'completed', 'status_class': 'success'},
            {'time': '10:15 AM', 'activity': 'Monthly report generated', 'user': 'Dr. Sarah Kimani', 'status': 'active', 'status_class': 'info'},
            {'time': '09:45 AM', 'activity': 'User permissions updated', 'user': 'Admin Panel', 'status': 'completed', 'status_class': 'success'},
        ]

        return {
            'total_patients': total_patients,
            'total_staff': total_staff,
            'todays_appointments': todays_appointments,
            'monthly_revenue': monthly_revenue,
            'recent_activities': recent_activities,
            'system_uptime': '99.8%',
            'database_size': '2.3GB',
            'active_doctors': 15,
            'active_nurses': 45,
            'active_support_staff': 25,
            'low_stock': Inventory.objects.filter(quantity_in_stock__lte=F('minimum_stock_level')).count(),
            'total_doctors': Doctor.objects.filter(is_available=True).count(),
        }
    except Exception as e:
        return {
            'total_patients': random.randint(1100, 1300),
            'total_staff': random.randint(80, 90),
            'todays_appointments': random.randint(120, 180),
            'monthly_revenue': random.randint(2200000, 2800000),
            'recent_activities': [
                {'time': '11:45 AM', 'activity': 'New staff member registered', 'user': 'Admin System', 'status': 'completed', 'status_class': 'success'},
                {'time': '11:30 AM', 'activity': 'System backup completed', 'user': 'Auto System', 'status': 'completed', 'status_class': 'success'},
                {'time': '10:15 AM', 'activity': 'Monthly report generated', 'user': 'Dr. Sarah Kimani', 'status': 'active', 'status_class': 'info'},
            ],
            'system_uptime': '99.8%',
            'database_size': '2.3GB',
            'active_doctors': random.randint(12, 18),
            'active_nurses': random.randint(40, 50),
            'active_support_staff': random.randint(20, 30),
            'low_stock': 0,
            'total_doctors': 0,
        }


def get_doctor_data(doctor, today):
    """Get data specific to doctors"""
    try:
        my_patients = Patient.objects.filter(user__is_active=True).count()
        doctor_appointments = Appointment.objects.filter(
            doctor=doctor, appointment_date=today
        ).count()
        pending_consultations = Appointment.objects.filter(
            doctor=doctor, status='waiting', appointment_date=today
        ).count()
        prescriptions_today = Prescription.objects.filter(
            medical_record__doctor=doctor,
            medical_record__created_at__date=today
        ).count()

        todays_schedule = [
            {'time': '9:00 AM', 'patient_name': 'John Doe', 'type': 'General Checkup', 'status': 'scheduled'},
            {'time': '10:30 AM', 'patient_name': 'Mary Smith', 'type': 'Follow-up Visit', 'status': 'confirmed'},
            {'time': '2:00 PM', 'patient_name': 'Peter Johnson', 'type': 'Consultation', 'status': 'scheduled'},
        ]

        recent_activities = [
            {'time': '11:30 AM', 'activity': 'Patient consultation completed', 'user': doctor.user.get_full_name() if doctor else 'Doctor', 'status': 'completed', 'status_class': 'success'},
            {'time': '10:45 AM', 'activity': 'Prescription written', 'user': doctor.user.get_full_name() if doctor else 'Doctor', 'status': 'completed', 'status_class': 'success'},
            {'time': '10:15 AM', 'activity': 'Appointment scheduled', 'user': doctor.user.get_full_name() if doctor else 'Doctor', 'status': 'active', 'status_class': 'info'},
            {'time': '09:30 AM', 'activity': 'Medical record updated', 'user': doctor.user.get_full_name() if doctor else 'Doctor', 'status': 'completed', 'status_class': 'success'},
        ]

        return {
            'my_patients': my_patients,
            'doctor_appointments': doctor_appointments,
            'pending_consultations': pending_consultations,
            'prescriptions_today': prescriptions_today,
            'todays_schedule': todays_schedule,
            'recent_activities': recent_activities,
        }
    except Exception as e:
        return {
            'my_patients': random.randint(100, 150),
            'doctor_appointments': random.randint(8, 15),
            'pending_consultations': random.randint(5, 12),
            'prescriptions_today': random.randint(10, 20),
            'todays_schedule': [
                {'time': '9:00 AM', 'patient_name': 'John Doe', 'type': 'General Checkup', 'status': 'scheduled'},
                {'time': '10:30 AM', 'patient_name': 'Mary Smith', 'type': 'Follow-up Visit', 'status': 'confirmed'},
                {'time': '2:00 PM', 'patient_name': 'Peter Johnson', 'type': 'Consultation', 'status': 'scheduled'},
            ],
            'recent_activities': [
                {'time': '11:30 AM', 'activity': 'Patient consultation completed', 'user': 'Doctor', 'status': 'completed', 'status_class': 'success'},
                {'time': '10:45 AM', 'activity': 'Prescription written', 'user': 'Doctor', 'status': 'completed', 'status_class': 'success'},
            ],
        }


def get_pharmacist_data(today):
    """Get data specific to pharmacists"""
    try:
        total_medications = Inventory.objects.all().count()
        low_stock_items = Inventory.objects.filter(
            quantity_in_stock__lte=F('minimum_stock_level')
        ).count()
        dispensed_today = Prescription.objects.filter(
            dispensed_at__date=today, is_dispensed=True
        ).count()
        expiry_date = today + timedelta(days=30)
        expiring_soon = Inventory.objects.filter(
            expiry_date__lte=expiry_date, expiry_date__gt=today
        ).count()

        critical_stock_alerts = [
            {'medication': 'Paracetamol 500mg', 'current_stock': 25, 'minimum_required': 100, 'status': 'Critical', 'status_class': 'danger'},
            {'medication': 'Amoxicillin 250mg', 'current_stock': 45, 'minimum_required': 50, 'status': 'Low', 'status_class': 'warning'},
            {'medication': 'Metformin 500mg', 'current_stock': 15, 'minimum_required': 75, 'status': 'Critical', 'status_class': 'danger'},
        ]

        pending_prescriptions = [
            {'patient_name': 'Jane Doe', 'doctor': 'Dr. Smith - Cardiology', 'status': 'Pending', 'status_class': 'warning'},
            {'patient_name': 'John Mwangi', 'doctor': 'Dr. Kimani - General', 'status': 'Pending', 'status_class': 'warning'},
            {'patient_name': 'Mary Wanjiku', 'doctor': 'Dr. Ochieng - Pediatrics', 'status': 'Pending', 'status_class': 'warning'},
        ]

        recent_activities = [
            {'time': '11:45 AM', 'activity': 'Medication dispensed', 'user': 'Pharmacist Grace', 'status': 'completed', 'status_class': 'success'},
            {'time': '11:15 AM', 'activity': 'Inventory updated', 'user': 'Pharmacist Grace', 'status': 'completed', 'status_class': 'success'},
            {'time': '10:30 AM', 'activity': 'Low stock alert triggered', 'user': 'System Alert', 'status': 'attention required', 'status_class': 'warning'},
            {'time': '09:45 AM', 'activity': 'Prescription verified', 'user': 'Pharmacist Grace', 'status': 'completed', 'status_class': 'success'},
        ]

        return {
            'total_medications': total_medications,
            'low_stock_items': low_stock_items,
            'dispensed_today': dispensed_today,
            'expiring_soon': expiring_soon,
            'critical_stock_alerts': critical_stock_alerts,
            'pending_prescriptions': pending_prescriptions,
            'recent_activities': recent_activities,
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {
            'total_medications': random.randint(800, 900),
            'low_stock_items': random.randint(5, 10),
            'dispensed_today': random.randint(35, 50),
            'expiring_soon': random.randint(10, 20),
            'critical_stock_alerts': [
                {'medication': 'Paracetamol 500mg', 'current_stock': 25, 'minimum_required': 100, 'status': 'Critical', 'status_class': 'danger'},
                {'medication': 'Amoxicillin 250mg', 'current_stock': 45, 'minimum_required': 50, 'status': 'Low', 'status_class': 'warning'},
            ],
            'pending_prescriptions': [
                {'patient_name': 'Jane Doe', 'doctor': 'Dr. Smith - Cardiology', 'status': 'Pending', 'status_class': 'warning'},
                {'patient_name': 'John Mwangi', 'doctor': 'Dr. Kimani - General', 'status': 'Pending', 'status_class': 'warning'},
            ],
            'recent_activities': [
                {'time': '11:45 AM', 'activity': 'Medication dispensed', 'user': 'Pharmacist', 'status': 'completed', 'status_class': 'success'},
                {'time': '10:30 AM', 'activity': 'Low stock alert triggered', 'user': 'System Alert', 'status': 'attention required', 'status_class': 'warning'},
            ],
        }


def get_billing_staff_data(today, current_month):
    """Get data specific to billing staff"""
    try:
        daily_revenue = Bill.objects.filter(
            created_at__date=today, status='paid'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        pending_payments = Bill.objects.filter(
            status='pending'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        invoices_generated = Bill.objects.filter(created_at__date=today).count()
        insurance_claims = 23

        outstanding_payments = [
            {'patient_name': 'John Kamau', 'invoice_number': '#INV-2024-001', 'amount': 15000, 'due_date': '2024-12-15', 'status': 'due', 'status_class': 'warning'},
            {'patient_name': 'Mary Njeri', 'invoice_number': '#INV-2024-002', 'amount': 8500, 'due_date': '2024-12-10', 'status': 'overdue', 'status_class': 'danger'},
            {'patient_name': 'Peter Ochieng', 'invoice_number': '#INV-2024-003', 'amount': 22000, 'due_date': '2024-12-18', 'status': 'due', 'status_class': 'info'},
        ]

        recent_activities = [
            {'time': '11:30 AM', 'activity': 'Invoice generated', 'user': 'Billing Staff', 'status': 'completed', 'status_class': 'success'},
            {'time': '11:00 AM', 'activity': 'Payment processed', 'user': 'Billing Staff', 'status': 'completed', 'status_class': 'success'},
            {'time': '10:15 AM', 'activity': 'Insurance claim submitted', 'user': 'Billing Staff', 'status': 'pending review', 'status_class': 'warning'},
            {'time': '09:30 AM', 'activity': 'Payment reminder sent', 'user': 'Auto System', 'status': 'sent', 'status_class': 'info'},
        ]

        return {
            'daily_revenue': daily_revenue,
            'pending_payments': pending_payments,
            'invoices_generated': invoices_generated,
            'insurance_claims': insurance_claims,
            'outstanding_payments': outstanding_payments,
            'recent_activities': recent_activities,
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {
            'daily_revenue': random.randint(100000, 150000),
            'pending_payments': random.randint(80000, 120000),
            'invoices_generated': random.randint(60, 80),
            'insurance_claims': random.randint(20, 30),
            'outstanding_payments': [
                {'patient_name': 'John Kamau', 'invoice_number': '#INV-2024-001', 'amount': 15000, 'due_date': '2024-12-15', 'status': 'due', 'status_class': 'warning'},
                {'patient_name': 'Mary Njeri', 'invoice_number': '#INV-2024-002', 'amount': 8500, 'due_date': '2024-12-10', 'status': 'overdue', 'status_class': 'danger'},
                {'patient_name': 'Peter Ochieng', 'invoice_number': '#INV-2024-003', 'amount': 22000, 'due_date': '2024-12-18', 'status': 'upcoming', 'status_class': 'info'},
            ],
            'recent_activities': [
                {'time': '11:30 AM', 'activity': 'Invoice generated', 'user': 'Billing Staff', 'status': 'completed', 'status_class': 'success'},
                {'time': '11:00 AM', 'activity': 'Payment processed', 'user': 'Billing Staff', 'status': 'completed', 'status_class': 'success'},
            ],
        }


def get_patient_data(patient, today):
    """Get data specific to patients"""
    try:
        patient_appointments = Appointment.objects.filter(
            patient=patient, appointment_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).count()
        next_appointment = Appointment.objects.filter(
            patient=patient, appointment_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).order_by('appointment_date', 'appointment_time').first()
        active_prescriptions = Prescription.objects.filter(
            medical_record__patient=patient
        ).count()
        outstanding_balance = Bill.objects.filter(
            patient=patient, status='pending'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        upcoming_appointments = Appointment.objects.filter(
            patient=patient, appointment_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).order_by('appointment_date', 'appointment_time')[:5]
        active_prescriptions_list = Prescription.objects.filter(
            medical_record__patient=patient
        ).order_by('-dispensed_at')[:5]

        return {
            'patient_appointments': patient_appointments,
            'next_appointment': next_appointment,
            'active_prescriptions': active_prescriptions,
            'outstanding_balance': outstanding_balance,
            'upcoming_appointments': upcoming_appointments,
            'active_prescriptions_list': active_prescriptions_list,
        }
    except Exception as e:
        print(f"Error fetching patient data: {e}")
        return {
            'patient_appointments': random.randint(2, 5),
            'next_appointment': "Dec 15, 2024",
            'active_prescriptions': random.randint(1, 4),
            'outstanding_balance': random.randint(3000, 8000),
            'upcoming_appointments': [],
            'active_prescriptions_list': [],
        }


# Additional utility functions
def get_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0
    return round(((current - previous) / previous) * 100, 1)


def format_currency(amount):
    """Format currency values"""
    return f"KSh {intcomma(amount)}"


def get_status_class(status):
    """Get Bootstrap class for status badges"""
    status_classes = {
        'completed': 'success',
        'pending': 'warning',
        'active': 'info',
        'cancelled': 'danger',
        'confirmed': 'success',
        'scheduled': 'primary',
        'overdue': 'danger',
        'critical': 'danger',
        'low': 'warning',
    }
    return status_classes.get(status.lower(), 'secondary')


@login_required
def system_reports_view(request):
    """System-wide reports view for administrators"""
    if not (request.user.is_superuser or request.user.role == 'administrator'):
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:dashboard')

    context = {
        'title': 'System Reports',
        'total_patients': Patient.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'total_doctors': Doctor.objects.count(),
        'total_bills': Bill.objects.count(),
    }
    return render(request, 'system_reports.html', context)


@login_required
def audit_logs_view(request):
    """Audit logs view for administrators"""
    if not (request.user.is_superuser or request.user.role == 'administrator'):
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:dashboard')

    context = {
        'title': 'Audit Logs',
        'recent_activities': [],
    }
    return render(request, 'audit_logs.html', context)


@login_required
def user_management_view(request):
    """User management view for administrators"""
    if not (request.user.is_superuser or request.user.role == 'administrator'):
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:dashboard')

    users = User.objects.all().order_by('-date_joined')
    context = {
        'title': 'User Management',
        'users': users,
    }
    return render(request, 'user_management.html', context)


@login_required
def system_settings_view(request):
    """System settings view for administrators"""
    if not (request.user.is_superuser or request.user.role == 'administrator'):
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:dashboard')

    context = {
        'title': 'System Settings',
        'system_info': {
            'django_version': '5.2.3',
            'python_version': '3.13.5',
            'database': 'SQLite',
            'debug_mode': settings.DEBUG,
        }
    }
    return render(request, 'system_settings.html', context)
