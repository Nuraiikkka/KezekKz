# KezekKz

Smart patient queue and wait-time app for clinics in Kazakhstan. A patient answers a few questions, gets the right specialist and urgency, books a slot and follows the live queue. The clinic staff manage the queue, patients and payments in a separate area.

## Features

**For patients**
- Short questionnaire (reason, symptoms, pain, red flags, allergies) that picks the specialist and the urgency
- Booking with the fastest available doctor of the specialty
- Live queue position, wait time and "when to leave home"
- Waiting list: free earlier slots are offered when someone cancels
- If the doctor is late, the patient chooses: wait, move the time or change the doctor
- Family: book a child or a parent from one profile, the doctor sees the age
- "I need help": wheelchair, escort, sign language interpreter, doctor's language; the clinic sees it in advance
- Profile with PIN or Telegram login: visit history, doctor notes and test results
- Payment after the visit: Kaspi, card, Apple Pay, Google Pay, cash, OSMS (demo, no real money)
- Rating with a comment
- Telegram notifications (optional)
- Russian, Kazakh and English

**For clinic staff** (separate area at `/staff`, login required)
- Live queue of every doctor, urgency control, visit statuses, doctor delay
- Patient cards with visit history, notes and test results
- Cash payments and revenue
- Analytics: no-shows, ratings, load by hour, visit time per doctor
- Waiting room board (`/board`) and QR poster (`/qr`)

## Tech stack

- Backend: Django, Django REST Framework, PostgreSQL
- Frontend: React, Vite, Tailwind CSS
- CI: GitHub Actions
- Deploy: Render (backend), Vercel (frontend)

## Project structure

```
backend/     Django API (apps, settings, requirements, tests)
frontend/    React app
render.yaml  Render deploy config
.github/     CI workflow
```

Branches: `main` has everything, `backend` and `frontend` have the two parts separately.

## Run locally

Backend (Python 3.11+, PostgreSQL):

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

Tests: `python manage.py test`. API docs: http://localhost:8000/api/docs/

Frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Deploy

1. Render: New - Blueprint - choose this repo (reads `render.yaml`).
2. In Render set `FRONTEND_URL` and `CSRF_TRUSTED_ORIGINS` to the Vercel address.
3. Vercel: Root Directory `frontend`, variable `VITE_API_URL` = `https://<render-name>.onrender.com/api`.
4. Optional Telegram: set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_BOT_USERNAME` in Render.

## Team

- Aitbazar Nuray - PM / QA
- Margulan Sharipzhan - Backend
- Kengesbay Assiya - Frontend
