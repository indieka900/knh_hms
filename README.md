# KNH HMS — Modernized Hospital Management System

Modernized in 2026: clean Tailwind-based design foundation, fixed broken modules, working DB/migrations, consistent roles, etc.

## Quick Start (Windows / pwsh)

```powershell
# from project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # choose administrator role

# Optional: create a few demo accounts (run in shell or use admin)
python manage.py runserver
```

Login at http://127.0.0.1:8000/ (default admin user example during dev: admin@knh.test / admin123 if created via script).

## Key Fixes Applied
- Full migrations + clean schema (no more "no such table").
- Signals consolidated, cross imports removed, safe profile creation for all roles/registration paths.
- All role checks normalized to 'administrator' (removed 'admin'/'nurse' ghosts).
- Appointment model lookups fixed (consistent use of `id` PK).
- Added full `patients/` list page (searchable, paginated, role-protected).
- Layout modernized: Tailwind CDN + config (navy/teal preserved), removed jQuery + Bootstrap 4/5 mismatch, killed the broken full-HTML `pop_up.html` include, clean messages toasts.
- Logout URLs, nav, and basic links repaired.
- Core flows (dashboard, patient list/create, appts, etc.) now render and navigate without crashes.

## Roles
patient | doctor | pharmacist | billing_staff | administrator

## Design Notes
- Primary layout now loads Tailwind via CDN for modern utility classes + the existing custom CSS for complex components (stats, timelines, print).
- Example modernized view: `/patients/` (new list) uses Tailwind cards + clean table.
- Further full sweep of every legacy Bootstrap class in other templates (appts, billing, medical, pharmacy, etc.) can be done incrementally — foundation is ready and new code should use Tailwind.
- Auth screens (login/register) still use their dedicated CSS but benefit from overall consistency improvements.

## What's Still Legacy / Next
- Some per-app templates and their inline/JS still contain old `btn-* form-control card row col-` classes (they render via the supplemental CSS).
- scripts.js has Bootstrap-specific patient search + modals (used in appointments create) — will need vanilla/Tailwind rewrite for full polish.
- No real email/SMS, advanced RBAC, or production config.

See MODERNIZATION_PLAN.md for the full original plan and phases.

Built with Django 5.2 + Tailwind. Happy managing!