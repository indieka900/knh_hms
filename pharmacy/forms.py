
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta

from .models import Pharmacist, Medicine, Inventory, MedicineDispensing
from medical_records.models import Patient, Prescription


class PharmacistForm(forms.ModelForm):
    """Form for creating/updating pharmacist records"""
    
    class Meta:
        model = Pharmacist
        fields = ['license_number']
        widgets = {
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter license number'
            }),
        }
    
    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if len(license_number) < 5:
            raise ValidationError('License number must be at least 5 characters long.')
        return license_number


class MedicineForm(forms.ModelForm):
    """Form for creating/updating medicine records"""
    
    class Meta:
        model = Medicine
        fields = ['name', 'generic_name', 'manufacturer', 'description', 'unit_of_measurement']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter medicine name',
                'required': True
            }),
            'generic_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter generic name (optional)'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter manufacturer name',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter medicine description (optional)'
            }),
            'unit_of_measurement': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('tablets', 'Tablets'),
                ('capsules', 'Capsules'),
                ('ml', 'Milliliters'),
                ('mg', 'Milligrams'),
                ('g', 'Grams'),
                ('vials', 'Vials'),
                ('bottles', 'Bottles'),
                ('strips', 'Strips'),
                ('boxes', 'Boxes'),
            ]),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise ValidationError('Medicine name must be at least 2 characters long.')
        return name.title()  # Capitalize first letter of each word


class InventoryForm(forms.ModelForm):
    """Form for creating/updating inventory records"""
    
    class Meta:
        model = Inventory
        fields = [
            'medicine', 'batch_number', 'quantity_in_stock', 'unit_price',
            'expiry_date', 'supplier', 'date_received', 'minimum_stock_level'
        ]
        widgets = {
            'medicine': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter batch number',
                'required': True
            }),
            'quantity_in_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter quantity',
                'required': True
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter unit price',
                'required': True
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier name',
                'required': True
            }),
            'date_received': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'minimum_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '10',
                'placeholder': 'Minimum stock level',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date_received to today
        if not self.instance.pk:
            self.fields['date_received'].initial = date.today()
    
    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date <= date.today():
            raise ValidationError('Expiry date must be in the future.')
        return expiry_date
    
    def clean_date_received(self):
        date_received = self.cleaned_data.get('date_received')
        if date_received and date_received > date.today():
            raise ValidationError('Date received cannot be in the future.')
        return date_received
    
    def clean_quantity_in_stock(self):
        quantity = self.cleaned_data.get('quantity_in_stock')
        if quantity and quantity < 1:
            raise ValidationError('Quantity must be at least 1.')
        return quantity
    
    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price and price < 0:
            raise ValidationError('Unit price cannot be negative.')
        return price


class DispensingForm(forms.ModelForm):
    """Form for dispensing medicines"""
    
    class Meta:
        model = MedicineDispensing
        fields = ['prescription', 'inventory_item', 'quantity_dispensed', 'notes']
        widgets = {
            'prescription': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'inventory_item': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'quantity_dispensed': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter quantity to dispense',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any additional notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter prescriptions to only show pending ones
        self.fields['prescription'].queryset = Prescription.objects.filter(
            status='pending'
        ).select_related('patient')
        
        # Filter inventory to only show items with stock > 0
        self.fields['inventory_item'].queryset = Inventory.objects.filter(
            quantity_in_stock__gt=0
        ).select_related('medicine')
        
        # Customize display labels
        self.fields['prescription'].label_from_instance = self.prescription_label
        self.fields['inventory_item'].label_from_instance = self.inventory_label
    
    def prescription_label(self, obj):
        return f"{obj.prescription_id} - {obj.patient.get_full_name()}"
    
    def inventory_label(self, obj):
        return f"{obj.medicine.name} (Stock: {obj.quantity_in_stock}, Batch: {obj.batch_number})"
    
    def clean(self):
        cleaned_data = super().clean()
        inventory_item = cleaned_data.get('inventory_item')
        quantity_dispensed = cleaned_data.get('quantity_dispensed')
        
        if inventory_item and quantity_dispensed:
            if quantity_dispensed > inventory_item.quantity_in_stock:
                raise ValidationError(
                    f'Cannot dispense {quantity_dispensed} units. '
                    f'Only {inventory_item.quantity_in_stock} units available in stock.'
                )
        
        return cleaned_data


class PatientSearchForm(forms.Form):
    """Form for searching patients"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, phone, or patient ID...',
            'autocomplete': 'off'
        })
    )


class PatientForm(forms.ModelForm):
    """Form for creating/updating patient records"""
    
    '''class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'date_of_birth', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address (optional)'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address (optional)'
            }),
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and len(phone) < 10:
            raise ValidationError('Phone number must be at least 10 digits long.')
        return phone
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            age = (date.today() - dob).days // 365
            if age > 150:
                raise ValidationError('Please enter a valid date of birth.')
            if age < 0:
                raise ValidationError('Date of birth cannot be in the future.')
        return dob'''


class InventoryUpdateForm(forms.ModelForm):
    """Form for updating inventory stock levels"""
    
    class Meta:
        model = Inventory
        fields = ['quantity_in_stock', 'minimum_stock_level']
        widgets = {
            'quantity_in_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Enter new quantity'
            }),
            'minimum_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter minimum stock level'
            }),
        }
    
    def clean_quantity_in_stock(self):
        quantity = self.cleaned_data.get('quantity_in_stock')
        if quantity is not None and quantity < 0:
            raise ValidationError('Quantity cannot be negative.')
        return quantity


class PrescriptionFilterForm(forms.Form):
    """Form for filtering prescriptions"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('dispensed', 'Dispensed'),
        ('cancelled', 'Cancelled'),
    ]
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search prescriptions...'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )