from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F

from patients.models import Patient
from appointments.models import Appointment, Doctor
from medical_records.models import Prescription, LabTest
from pharmacy.models import Inventory
from billing.models import Bill, Payment
from notifications.models import Notification


@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()
    now = timezone.now()

    todays_appointments = Appointment.objects.filter(appointment_date=today)
    if user.role == 'doctor':
        try:
            doctor = Doctor.objects.get(user=user)
            todays_appointments = todays_appointments.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            todays_appointments = todays_appointments.none()
    elif user.role == 'patient':
        try:
            patient = Patient.objects.get(user=user)
            todays_appointments = todays_appointments.filter(patient=patient)
        except Patient.DoesNotExist:
            todays_appointments = todays_appointments.none()

    recent_appointments = todays_appointments.select_related(
        'patient__user', 'doctor__user'
    ).order_by('appointment_time')[:8]

    low_stock = Inventory.objects.filter(
        quantity_in_stock__lte=F('minimum_stock_level')
    ).count()

    context = {
        'title': 'Dashboard',
        'today': today,
        'todays_count': todays_appointments.count(),
        'total_patients': Patient.objects.count(),
        'total_doctors': Doctor.objects.filter(is_available=True).count(),
        'low_stock': low_stock,
        'pending_bills_amount': Bill.objects.filter(
            status__in=['pending', 'partial']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'revenue_today': Payment.objects.filter(
            payment_date__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'revenue_month': Payment.objects.filter(
            payment_date__month=now.month,
            payment_date__year=now.year
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'recent_appointments': recent_appointments,
        'unread_notifications': Notification.objects.filter(
            recipient=user, status__in=['pending', 'sent']
        ).count(),
        'pending_rx': Prescription.objects.filter(is_dispensed=False).count(),
        'pending_labs': LabTest.objects.filter(status='pending').count(),
        'overdue_bills': Bill.objects.filter(status='overdue').count(),
    }
    return render(request, 'dashboard.html', context)
