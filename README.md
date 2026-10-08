# KezekKz - TSIS 5

Smart patient queue for clinics.

## What we did in TSIS 5

We wrote the project charter and started the real coding:

- API for the questions: the patient answers and gets a suggested doctor and urgency (routine, priority or urgent)
- API for booking a time slot. Every booking gets a queue number, a position and a wait time
- Staff API: login with a token, see the queue of a doctor, confirm urgency, change status
- React pages: home, questions, booking and tracking
- API documentation: http://localhost:8000/api/docs/
- Tests for the API

Important: the app only gives a suggestion. Staff always confirm the urgency. We don't save any diagnosis.

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
