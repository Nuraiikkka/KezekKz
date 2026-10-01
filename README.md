# KezekKz — Smart Patient Queue and Wait-Time Assistant

Booking + intake + live queue assistant for small and mid-size private clinics in Kazakhstan.
Course project (IT Project Management, Group 1).

**Stack:** Django 5 + Django REST Framework + PostgreSQL (backend) · React 19 + Vite + Tailwind + React Router + Axios (frontend) · GitHub Actions (CI)

## Current scope (Sprint 2: 29 Sep – 12 Oct)

| Area | Status |
|---|---|
| Repo, CI (GitHub Actions: tests + migrations check + lint + build) | done |
| DB schema: clinic, specialty, doctor, time slot, intake, patient, appointment | done |
| Intake questionnaire (8 questions) + urgency/specialist routing suggestion | done |
| Patient booking API + basic queue numbering, position & wait estimate | done |
| Patient tracking page (live position, auto-refresh, cancel) | done |
| Staff API foundation (token auth, doctor queue, confirm urgency, status changes) | done |
| Staff dashboard UI, delay recalculation, notifications, no-show → waitlist | Sprint 3+ |

API documentation:
- Interactive (Swagger, try requests in the browser): http://localhost:8000/api/docs/
- ReDoc (read-only view): http://localhost:8000/api/redoc/
- OpenAPI schema: http://localhost:8000/api/schema/
- Written contract and routing rules: [docs/API.md](docs/API.md)

## Privacy rules (from the Charter)

- Routing output is a **suggestion only**; staff always confirm urgency.
- No diagnoses or health history are stored. The optional allergies/conditions answer is accepted but **not persisted**.
- Patients see their appointment only via a random tracking token; the public view shows only their first name.

## Run locally

Requirements: Python 3.11+, Node 20+, PostgreSQL.

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL if needed
createdb kezek
python manage.py migrate
python manage.py seed_demo    # pilot clinic, 4 specialties, 5 doctors, 7 days of slots, staff user "reception"
python manage.py runserver
```

API at http://localhost:8000/api/, admin at http://localhost:8000/admin/
(create an admin with `python manage.py createsuperuser`).

Tests:

```bash
python manage.py test
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173.

## Project structure

```
backend/
  config/                 Django settings & URLs
  apps/clinics/           Clinic, Specialty, Doctor, TimeSlot + seed_demo command
  apps/intake/            questionnaire.py (questions), routing.py (urgency rules), IntakeSubmission
  apps/appointments/      Patient, Appointment, queue.py (numbering + wait estimate), staff endpoints
frontend/src/
  api/                    Axios client + endpoint functions
  pages/                  Home → Intake → Booking → Track
  components/             Layout + small UI kit
docs/API.md               API contract
.github/workflows/ci.yml  CI pipeline
```

## Team

- Aitbazar Nuray — PM / QA (Data)
- Margulan Sharipzhan — Backend
- Kengesbay Assiya — Frontend
