# KezekKz backend

Django + Django REST Framework + PostgreSQL.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env
createdb kezek
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Tests: `python manage.py test`

API docs: http://localhost:8000/api/docs/
