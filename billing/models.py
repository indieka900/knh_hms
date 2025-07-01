from django.db import models
from django.conf import settings
from patients.models import Patient
from appointments.models import Appointment
from pharmacy.models import MedicineDispensing

class BillingStaff(models.Model):
    staff_id = models.CharField(max_length=15, unique=True, primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, default='Billing')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.user.role != 'billing_staff':
            raise ValueError("User role must be 'billing_staff' to create BillingStaff profile")
        
        if not self.staff_id:
            self.staff_id = f"BS{self.user.id:06d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Billing Staff"

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Bill(models.Model):
    BILL_STATUS = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    bill_id = models.CharField(max_length=20, unique=True, primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=BILL_STATUS, default='pending')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    created_by = models.ForeignKey(BillingStaff, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid
    
    def __str__(self):
        return f"Bill {self.bill_id} - {self.patient.user.get_full_name()}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile_money', 'Mobile Money'),
        ('insurance', 'Insurance'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    payment_id = models.CharField(max_length=20, unique=True, primary_key=True)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS)
    transaction_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(BillingStaff, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment {self.payment_id} - KES {self.amount}"
    
model_admin = [
    ServiceType, Bill,
    BillItem, Payment
]