# KezekKz - TSIS 3

Smart patient queue for clinics.

## What we did in TSIS 3

- We chose our tech stack:
  - backend: Django + Django REST Framework + PostgreSQL
  - frontend: React + Vite + Tailwind
- We made the repo and the folders for backend and frontend
- We wrote the 8 questions for the patient (`backend/apps/intake/questionnaire.py`)
- We wrote the first urgency rules (`backend/apps/intake/routing.py`) and small tests for them
- CI/CD is not ready yet, it took more time to choose a tool than we thought

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
python manage.py test
python manage.py runserver
```

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
