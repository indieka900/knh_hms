from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import date, datetime, timedelta
import random
from faker import Faker

from accounts.models import User
from patients.models import Patient
from appointments.models import Doctor, Appointment, DoctorSchedule
from medical_records.models import MedicalRecord, Prescription
from billing.models import Bill, BillItem, ServiceType, BillingStaff, Payment
from pharmacy.models import Pharmacist, Medicine

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Generate seed data for the KNH HMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=100,
            help='Number of patients to create (default: 100)'
        )
        parser.add_argument(
            '--doctors',
            type=int,
            default=15,
            help='Number of doctors to create (default: 15)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        # Create service types first
        self.create_service_types()
        
        # Create medicines
        self.create_medicines()
        
        # Create staff users
        self.create_administrators()
        self.create_billing_staff()
        self.create_pharmacists()
        self.create_doctors(options['doctors'])
        
        # Create patients
        self.create_patients(options['patients'])
        
        # Create appointments
        self.create_appointments()
        
        # Create medical records
        self.create_medical_records()
        
        # Create bills and payments
        self.create_bills_and_payments()

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with realistic data!')
        )

    def clear_data(self):
        """Clear existing data"""
        models_to_clear = [
            Payment, BillItem, Bill, Prescription, MedicalRecord, 
            Appointment, DoctorSchedule, Medicine, ServiceType,
            Patient, Doctor, BillingStaff, Pharmacist, User
        ]
        
        for model in models_to_clear:
            try:
                count = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'Cleared {count} {model.__name__} records')
            except Exception as e:
                self.stdout.write(f'Error clearing {model.__name__}: {e}')

    def create_service_types(self):
        """Create medical service types"""
        services = [
            ('Consultation', 2500.00, 'General medical consultation'),
            ('Specialist Consultation', 5000.00, 'Specialist doctor consultation'),
            ('X-Ray', 3000.00, 'X-Ray imaging service'),
            ('Blood Test', 1500.00, 'Complete blood count and analysis'),
            ('ECG', 2000.00, 'Electrocardiogram test'),
            ('Ultrasound', 4000.00, 'Ultrasound imaging'),
            ('CT Scan', 15000.00, 'CT scan imaging'),
            ('MRI', 25000.00, 'Magnetic resonance imaging'),
            ('Surgery - Minor', 50000.00, 'Minor surgical procedures'),
            ('Surgery - Major', 150000.00, 'Major surgical procedures'),
            ('Pharmacy', 0.00, 'Medication dispensing'),
            ('Emergency Treatment', 10000.00, 'Emergency medical treatment'),
        ]
        
        for name, price, description in services:
            ServiceType.objects.get_or_create(
                name=name,
                defaults={'base_price': price, 'description': description}
            )
        
        self.stdout.write(f'Created {len(services)} service types')

    def create_medicines(self):
        """Create medicine inventory"""
        medicines = [
            ('Paracetamol 500mg', 'Tablet', 50.00, 1000, 100, '2025-12-31'),
            ('Amoxicillin 250mg', 'Capsule', 150.00, 500, 50, '2025-06-30'),
            ('Metformin 500mg', 'Tablet', 80.00, 800, 75, '2026-03-15'),
            ('Aspirin 100mg', 'Tablet', 25.00, 1500, 150, '2025-09-20'),
            ('Omeprazole 20mg', 'Capsule', 200.00, 300, 30, '2025-11-10'),
            ('Atorvastatin 20mg', 'Tablet', 350.00, 200, 20, '2026-01-25'),
            ('Lisinopril 10mg', 'Tablet', 120.00, 400, 40, '2025-08-15'),
            ('Amlodipine 5mg', 'Tablet', 100.00, 600, 60, '2025-12-05'),
            ('Insulin Regular', 'Injection', 2500.00, 50, 5, '2025-07-30'),
            ('Salbutamol Inhaler', 'Inhaler', 800.00, 100, 10, '2025-10-12'),
        ]
        
        for name, form, price, stock, min_stock, expiry in medicines:
            Medicine.objects.get_or_create(
                name=name,
                defaults={
                    'generic_name': name.split()[0],
                    'manufacturer': fake.company(),
                    'description': f'{form} medication for medical treatment',
                    'unit_of_measurement': form
                }
            )
        
        self.stdout.write(f'Created {len(medicines)} medicines')

    def create_administrators(self):
        """Create administrator accounts"""
        admin_data = [
            ('admin@knhhms.co.ke', 'Admin', 'User', '+254701234567'),
            ('director@knhhms.co.ke', 'Medical', 'Director', '+254701234568'),
        ]
        
        for email, first_name, last_name, phone in admin_data:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='admin123',
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone,
                    role='administrator',
                    date_of_birth=fake.date_of_birth(minimum_age=30, maximum_age=60),
                    address=fake.address()
                )
        
        self.stdout.write(f'Created {len(admin_data)} administrators')

    def create_billing_staff(self):
        """Create billing staff accounts"""
        for i in range(5):
            email = f'billing{i+1}@knhhms.co.ke'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='billing123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    role='billing_staff',
                    date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=55),
                    address=fake.address()
                )
                
                # Only create if doesn't exist
                if not hasattr(user, 'billingstaff'):
                    BillingStaff.objects.create(
                        user=user,
                        department='Billing'
                    )
        
        self.stdout.write('Created 5 billing staff members')

    def create_pharmacists(self):
        """Create pharmacist accounts"""
        for i in range(3):
            email = f'pharmacist{i+1}@knhhms.co.ke'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='pharma123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    role='pharmacist',
                    date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=55),
                    address=fake.address()
                )
                
                # Only create if doesn't exist
                if not hasattr(user, 'pharmacist'):
                    Pharmacist.objects.create(
                        user=user,
                        license_number=f'PHARM{random.randint(10000, 99999)}'
                    )
        
        self.stdout.write('Created 3 pharmacists')

    def create_doctors(self, count):
        """Create doctor accounts"""
        specializations = [
            'Cardiology', 'Dermatology', 'Emergency Medicine', 'Family Medicine',
            'Internal Medicine', 'Neurology', 'Obstetrics and Gynecology',
            'Pediatrics', 'Psychiatry', 'Radiology', 'Surgery', 'Orthopedics',
            'Oncology', 'Anesthesiology', 'Pathology'
        ]
        
        for i in range(count):
            email = f'doctor{i+1}@knhhms.co.ke'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='doctor123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    role='doctor',
                    date_of_birth=fake.date_of_birth(minimum_age=28, maximum_age=65),
                    address=fake.address()
                )
                
                # Only create if doesn't exist
                if not hasattr(user, 'doctor'):
                    doctor = Doctor.objects.create(
                        user=user,
                        license_number=f'DOC{random.randint(10000, 99999)}',
                        specialization=random.choice(specializations),
                        years_of_experience=random.randint(1, 35),
                        consultation_fee=random.randint(2000, 8000),
                        is_available=True
                    )
                else:
                    doctor = user.doctor
                
                # Create doctor schedules
                self.create_doctor_schedule(doctor)
        
        self.stdout.write(f'Created {count} doctors')

    def create_doctor_schedule(self, doctor):
        """Create weekly schedule for a doctor"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        working_days = random.sample(days, random.randint(4, 6))
        
        for day in working_days:
            start_time = random.choice(['08:00', '09:00', '10:00'])
            end_time = random.choice(['16:00', '17:00', '18:00'])
            
            DoctorSchedule.objects.create(
                doctor=doctor,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                is_active=True
            )

    def create_patients(self, count):
        """Create patient accounts"""
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        insurance_providers = [
            'NHIF', 'AAR Insurance', 'Jubilee Insurance', 'CIC Insurance',
            'Madison Insurance', 'Liberty Life', 'Britam', 'UAP Insurance'
        ]
        
        for i in range(count):
            email = f'patient{i+1}@example.com'
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='patient123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    role='patient',
                    date_of_birth=fake.date_of_birth(minimum_age=1, maximum_age=90),
                    address=fake.address()
                )
                
                # Patient profile will be created automatically by signal
                try:
                    patient = Patient.objects.get(user=user)
                    patient.gender = random.choice(['M', 'F'])
                    patient.blood_group = random.choice(blood_groups)
                    patient.emergency_contact_name = fake.name()
                    patient.emergency_contact_phone = f'+2547{random.randint(10000000, 99999999)}'
                    patient.emergency_contact_relationship = random.choice(['Spouse', 'Parent', 'Sibling', 'Child', 'Friend'])
                    
                    if random.choice([True, False]):
                        patient.insurance_provider = random.choice(insurance_providers)
                        patient.insurance_number = f'INS{random.randint(100000, 999999)}'
                    
                    if random.choice([True, False]):
                        patient.allergies = fake.sentence(nb_words=6)
                    
                    if random.choice([True, False]):
                        patient.chronic_conditions = fake.sentence(nb_words=8)
                    
                    patient.save()
                except Patient.DoesNotExist:
                    self.stdout.write(f'Warning: Patient profile not created for {email}')
        
        self.stdout.write(f'Created {count} patients')

    def create_appointments(self):
        """Create appointments for the last 30 days and next 30 days"""
        doctors = list(Doctor.objects.all())
        patients = list(Patient.objects.all())
        
        if not doctors or not patients:
            self.stdout.write(self.style.WARNING('No doctors or patients found for appointments'))
            return
        
        statuses = ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']
        reasons = [
            'General checkup', 'Follow-up consultation', 'Symptom evaluation',
            'Routine examination', 'Specialist consultation', 'Emergency visit',
            'Vaccination', 'Test results review', 'Prescription renewal',
            'Health screening', 'Injury assessment', 'Chronic disease management'
        ]
        
        appointment_count = 0
        
        # Create appointments for the last 30 days
        for _ in range(200):
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            
            # Generate appointment date in the last 30 days
            appointment_date = fake.date_between(start_date='-30d', end_date='today')
            appointment_time = fake.time_object()
            
            # Past appointments are more likely to be completed
            status = random.choices(
                statuses,
                weights=[10, 15, 60, 10, 5],  # Higher weight for completed
                k=1
            )[0]
            
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=status,
                reason=random.choice(reasons),
                notes=fake.sentence() if random.choice([True, False]) else ''
            )
            appointment_count += 1
        
        # Create future appointments
        for _ in range(100):
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            
            # Generate appointment date in the next 30 days
            appointment_date = fake.date_between(start_date='today', end_date='+30d')
            appointment_time = fake.time_object()
            
            # Future appointments are scheduled or confirmed
            status = random.choice(['scheduled', 'confirmed'])
            
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=status,
                reason=random.choice(reasons),
                notes=fake.sentence() if random.choice([True, False]) else ''
            )
            appointment_count += 1
        
        self.stdout.write(f'Created {appointment_count} appointments')

    def create_medical_records(self):
        """Create medical records for completed appointments"""
        completed_appointments = Appointment.objects.filter(status='completed')
        
        diagnoses = [
            'Hypertension', 'Type 2 Diabetes', 'Upper Respiratory Infection',
            'Gastroenteritis', 'Migraine', 'Lower Back Pain', 'Anxiety Disorder',
            'Allergic Rhinitis', 'Hyperlipidemia', 'Asthma', 'Osteoarthritis',
            'Depression', 'Urinary Tract Infection', 'Anemia', 'Insomnia'
        ]
        
        symptoms = [
            'Headache, fatigue', 'Chest pain, shortness of breath', 'Nausea, vomiting',
            'Fever, cough', 'Joint pain, stiffness', 'Dizziness, weakness',
            'Abdominal pain, diarrhea', 'Skin rash, itching', 'Sleep disturbance',
            'Memory problems, confusion', 'Muscle weakness, pain'
        ]
        
        treatments = [
            'Medication prescribed, lifestyle modifications recommended',
            'Physical therapy, pain management', 'Dietary changes, exercise program',
            'Antibiotics prescribed, rest recommended', 'Stress management, counseling',
            'Regular monitoring, medication adjustment', 'Surgery scheduled',
            'Home care instructions, follow-up in 2 weeks'
        ]
        
        record_count = 0
        
        for appointment in completed_appointments[:150]:  # Create records for 150 appointments
            record = MedicalRecord.objects.create(
                patient=appointment.patient,
                doctor=appointment.doctor,
                appointment=appointment,
                diagnosis=random.choice(diagnoses),
                symptoms=random.choice(symptoms),
                treatment_plan=random.choice(treatments),
                notes=fake.text(max_nb_chars=200),
                follow_up_date=fake.date_between(start_date='today', end_date='+90d') if random.choice([True, False]) else None
            )
            
            # Create prescriptions for some medical records
            if random.choice([True, False]):
                self.create_prescriptions(record)
            
            record_count += 1
        
        self.stdout.write(f'Created {record_count} medical records')

    def create_prescriptions(self, medical_record):
        """Create prescriptions for a medical record"""
        medicines = list(Medicine.objects.all())
        
        if not medicines:
            return
        
        # Create 1-3 prescriptions per medical record
        prescription_count = random.randint(1, 3)
        
        for _ in range(prescription_count):
            medicine = random.choice(medicines)
            
            Prescription.objects.create(
                medical_record=medical_record,
                medication_name=medicine.name,
                dosage=f'{random.randint(250, 1000)}mg',
                frequency=f'{random.randint(1, 3)} times daily',
                duration=f'{random.randint(7, 30)} days',
                instructions=f'Take {random.choice(["with food", "before meals", "after meals", "as needed"])}',
                is_dispensed=random.choice([True, False])
            )

    def create_bills_and_payments(self):
        """Create bills and payments for appointments"""
        appointments = Appointment.objects.filter(status='completed')
        billing_staff = list(BillingStaff.objects.all())
        service_types = list(ServiceType.objects.all())
        
        if not billing_staff or not service_types:
            self.stdout.write(self.style.WARNING('No billing staff or service types found'))
            return
        
        bill_count = 0
        payment_count = 0
        
        for appointment in appointments[:120]:  # Create bills for 120 appointments
            bill = Bill.objects.create(
                patient=appointment.patient,
                appointment=appointment,
                total_amount=0,  # Will be calculated from items
                due_date=appointment.appointment_date + timedelta(days=30),
                created_by=random.choice(billing_staff),
                notes=fake.sentence() if random.choice([True, False]) else ''
            )
            
            # Add 1-4 bill items
            total_amount = 0
            item_count = random.randint(1, 4)
            
            for _ in range(item_count):
                service = random.choice(service_types)
                quantity = random.randint(1, 3)
                unit_price = service.base_price
                
                BillItem.objects.create(
                    bill=bill,
                    service_type=service,
                    description=service.description,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=quantity * unit_price
                )
                
                total_amount += quantity * unit_price
            
            bill.total_amount = total_amount
            
            # Randomly set bill status and payments
            status_choice = random.choices(
                ['paid', 'pending', 'partial', 'overdue'],
                weights=[60, 20, 15, 5],
                k=1
            )[0]
            
            if status_choice == 'paid':
                bill.amount_paid = total_amount
                bill.status = 'paid'
                
                # Create payment record
                Payment.objects.create(
                    bill=bill,
                    amount=total_amount,
                    payment_method=random.choice(['cash', 'card', 'mobile_money', 'insurance']),
                    transaction_reference=f'TXN{random.randint(100000, 999999)}',
                    processed_by=random.choice(billing_staff)
                )
                payment_count += 1
                
            elif status_choice == 'partial':
                bill.amount_paid = total_amount * random.uniform(0.3, 0.8)
                bill.status = 'partial'
                
                # Create partial payment record
                Payment.objects.create(
                    bill=bill,
                    amount=bill.amount_paid,
                    payment_method=random.choice(['cash', 'card', 'mobile_money']),
                    transaction_reference=f'TXN{random.randint(100000, 999999)}',
                    processed_by=random.choice(billing_staff)
                )
                payment_count += 1
                
            elif status_choice == 'overdue':
                bill.status = 'overdue'
                bill.due_date = fake.date_between(start_date='-30d', end_date='-1d')
            else:
                bill.status = 'pending'
            
            bill.save()
            bill_count += 1
        
        self.stdout.write(f'Created {bill_count} bills and {payment_count} payments')
