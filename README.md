# BookShelf

BookShelf is a Goodreads-style Django application for browsing books, managing
personal shelves, rating and reviewing books, and receiving offline TF-IDF
recommendations.

## Stack

- Python 3.10+
- Django 5
- PostgreSQL with `psycopg2`
- Plain Django templates, HTML, CSS, and JavaScript
- Open Library data and covers
- scikit-learn and pandas for recommendations

## Local setup

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a PostgreSQL database named `bookshelf`, copy the local environment
settings into `.env`, and adjust the database credentials:

```text
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=
DB_NAME=bookshelf
DB_USER=your-postgres-user
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432
```

Run migrations and start the development server:

```powershell
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Import books and build recommendations

Import a small test set:

```powershell
python manage.py import_openlibrary fantasy --limit 50 --no-descriptions
```

Build the TF-IDF similarity rows:

```powershell
python manage.py build_recommendations --top-k 10
```

## Tests

```powershell
python manage.py test books
```

The PostgreSQL role used for tests needs permission to create temporary test
databases.

## Deployment

```text
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn bookshelf.wsgi
```

Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and
the PostgreSQL `DB_*` variables on the host. Never commit `.env`.

See [previous.md](previous.md) for the detailed implementation handoff and
completed step history. The original build specification is in
[instruction_Ai.md](instruction_Ai.md).
