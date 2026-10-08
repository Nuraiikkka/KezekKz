# KezekKz - TSIS 4

Smart patient queue for clinics.

## What we did in TSIS 4

- We finished CI with GitHub Actions. Now tests and build run on every push
- We made the database models: Clinic, Specialty, Doctor, TimeSlot, Intake, Patient and Appointment
- We added a command `seed_demo`. It adds a test clinic with 4 specialties, 5 doctors and free time slots
- Margulan showed Nuray and Assiya how the database and API work, so not only one person knows it

## Folders

```
backend/
  apps/          our django apps
  settings/      base.py, conf.py, env/local.py, env/prod.py, urls.py
  requirements/  base.txt, dev.txt, prod.txt
  logs/
frontend/        react app
```

## How to run

Backend (you need Python 3.11+ and PostgreSQL):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env
createdb kezek
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

You can see all the data in the admin page: http://localhost:8000/admin/

Frontend (you need Node 20+):

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173

## Team

- Aitbazar Nuray - PM / QA
- Margulan Sharipzhan - Backend
- Kengesbay Assiya - Frontend
