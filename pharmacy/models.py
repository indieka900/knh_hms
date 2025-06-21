from django.db import models
from django.conf import settings
from medical_records.models import Prescription

class Pharmacist(models.Model):
    pharmacist_id = models.CharField(max_length=15, unique=True, primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Pharmacist"

class Medicine(models.Model):
    # medicine_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    unit_of_measurement = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.generic_name})"

class Inventory(models.Model):
    # inventory_id = models.CharField(max_length=20, unique=True, primary_key=True)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='inventory_items')
    batch_number = models.CharField(max_length=50)
    quantity_in_stock = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    supplier = models.CharField(max_length=100)
    date_received = models.DateField()
    minimum_stock_level = models.PositiveIntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Inventories"
    
    def __str__(self):
        return f"{self.medicine.name} - Batch: {self.batch_number}"

class MedicineDispensing(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    inventory_item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    pharmacist = models.ForeignKey(Pharmacist, on_delete=models.CASCADE)
    quantity_dispensed = models.PositiveIntegerField()
    dispensed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Dispensed: {self.inventory_item.medicine.name} - {self.quantity_dispensed} units"