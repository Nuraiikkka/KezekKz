# KezekKz - TSIS 6-7

Smart patient queue for clinics.

## What we did in TSIS 6-7

- We wrote 10 user stories (US-01 ... US-10) with Given / When / Then scenarios
- We made tests from the scenarios of Sprint 1 (US-01, US-02, US-03) - see `backend/apps/appointments/test_user_stories.py`
- We changed the error messages so they are the same as in our stories ("This slot is not free anymore", "Phone number is required")
- If the patient says "Not sure" about the doctor, the app chooses the doctor from the reason of the visit
- The tracking page updates every 10 seconds and shows "No active appointment" if the link is wrong

## What is next

| Sprint | Stories |
|---|---|
| 2 (13 - 26 Oct) | US-05 queue position, US-07 staff dashboard, US-04 staff confirms urgency, US-06 alert before the turn |
| 3 (27 Oct - 9 Nov) | US-08 cancel, US-09 doctor is late, US-10 possible no-show |

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
python manage.py runserver
```

Run tests: `python manage.py test`

API documentation: http://localhost:8000/api/docs/

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
