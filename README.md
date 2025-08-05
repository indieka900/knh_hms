# Django Hospital Managegement System 🛍️

A fully-featured hospital management system built with Django, designed to streamline hospital operations and enhance patient care.

[![GitHub Stars](https://img.shields.io/github/stars/indieka900/knh_hms?style=social)](https://github.com/indieka900/knh_hms/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/indieka900/knh_hms?style=social)](https://github.com/indieka900/knh_hms/network/members)
[![GitHub Follow](https://img.shields.io/github/followers/indieka900?style=social)](https://github.com/indieka900)

## ✨ Features

### Appointment Management

- Book appointments with doctors
- View upcoming appointments
- Cancel appointments
- Receive appointment reminders via email
- Doctor availability management
- Patient appointment history
- Doctor's schedule management
- Appointment status tracking (confirmed, pending, cancelled)

### Patient Management

- Patient registration
- Patient profile management
- Medical history tracking
- Prescription management
- Patient appointment history
- Patient notifications (email/SMS)
- Patient feedback system

### Billing and Payments

- Generate invoices
- Payment processing
- Payment history
- Payment methods:
  - Credit/Debit Card
  - PayPal
  - M-PESA

## 🚀 Installation

1. Clone the repository

```bash
git clone https://github.com/indieka900/knh_hms.git/
cd knh_hms
```

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations

```bash
python manage.py migrate
```

6. Create a superuser

```bash
python manage.py createsuperuser
```

7. Run the development server

```bash
python manage.py runserver
```
