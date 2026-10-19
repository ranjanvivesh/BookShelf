# BookShelf Project Handoff

This file is the persistent progress record for the BookShelf build described in
[`instruction_Ai.md`](./instruction_Ai.md). Update it after every completed step
so a different AI can continue without guessing what has already been done.

Detailed Step 1 documentation is available in
[`step1.md`](./step1.md).

## Project purpose and fixed technical decisions

BookShelf is a small Goodreads-style website. Users will eventually browse and
search books, place books on shelves, rate and review them, and receive
recommendations from an offline TF-IDF model.

The fixed stack from `instruction_Ai.md` is:

- Python 3.10+ and Django 5.
- PostgreSQL using `psycopg2`.
- Django function-based views only.
- Plain HTML, CSS, and JavaScript in Django templates.
- No React, CSS framework, npm, or REST API.
- scikit-learn and pandas for machine learning.
- Open Library API for book data and covers.
- Apps: `books`, `library`, and `recommender`.
- All ML code must remain in `recommender/services.py`.

## Completed work

### Step 1 — Project setup and PostgreSQL

Status: **Completed and validated.**

Created in the workspace:

- `venv\` — Python virtual environment.
- `manage.py` — Django management entry point.
- `bookshelf\` — Django project package, including `settings.py`, URLs, WSGI,
  and ASGI modules.
- `books\` — empty Django app scaffold.
- `library\` — empty Django app scaffold.
- `recommender\` — empty Django app scaffold.
- `templates\` — top-level template directory.
- `static\` — top-level static directory.
- `requirements.txt` — installed dependency lock snapshot.
- `.env` — local development configuration; ignored by Git.
- `.gitignore` — ignores `.env`, `venv/`, Python cache files, SQLite fallback
  files, and collected static output.

Installed into `venv`:

- Django 5.2.18
- psycopg2-binary 2.9.13
- python-dotenv 1.2.4
- pandas 3.0.6
- scikit-learn 1.9.1
- requests 2.34.2
- Their transitive dependencies, recorded in `requirements.txt`.

Configured in `bookshelf/settings.py`:

- Loads `.env` with `python-dotenv`.
- Reads `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` from environment variables.
- Uses PostgreSQL and reads `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and
  `DB_PORT` from environment variables.
- Adds `django.contrib.postgres`, `books`, `library`, and `recommender` to
  `INSTALLED_APPS`.
- Uses the top-level `templates\` directory.
- Uses the top-level `static\` directory.
- Sets `LOGIN_REDIRECT_URL` and `LOGOUT_REDIRECT_URL` to `/`.

The current `.env` contains example local values:

```text
DB_NAME=bookshelf
DB_USER=vivesh
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
```

Replace `DB_USER` and `DB_PASSWORD` if the local PostgreSQL installation uses
different credentials. Do not commit `.env`.

## Validation status

Completed:

- Created the virtual environment successfully.
- Installed the required dependencies successfully.
- Generated the Django project and all three app scaffolds.
- Generated `requirements.txt`.

Not completed:

- No Step 1 work remains.

Note: the `psql` command was not available in the shell, but the configured
PostgreSQL server accepted the Django connection and migrations successfully.

## Step 1 verification record

From `d:\_____WORK_____\BookR` in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

The configured database was already available, so no database creation command
was needed during this run. If setting up another machine, create the empty
database using a PostgreSQL role that has permission to create databases:

```sql
CREATE DATABASE bookshelf;
```

After ensuring `.env` matches the PostgreSQL role, run:

```powershell
python manage.py migrate
python manage.py runserver
```

Expected results:

- `migrate` completes without database connection or migration errors.
- `runserver` starts successfully and the Django welcome page is available at
  `http://127.0.0.1:8000/`.

Actual verification completed on 2026-10-19:

- `.\venv\Scripts\python.exe manage.py check` — passed with no issues.
- `.\venv\Scripts\python.exe manage.py migrate --noinput` — passed; Django
  applied the admin, auth, contenttypes, and sessions migrations.
- `.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload` —
  started successfully.
- `Invoke-WebRequest http://127.0.0.1:8000/` — returned HTTP 200 and the
  Django welcome page. The temporary development server was stopped after the
  check.

### Step 2 — Database models

Status: **Completed and validated.**

Implemented the requested models:

- `books/models.py`
  - `Author` with a unique name.
  - `Genre` with a unique slug and alphabetical ordering by name.
  - `Book` with title, many-to-many authors and genres, optional description,
    unique nullable Open Library work key, optional cover ID and publication
    year, and automatic creation time.
  - `Book` is ordered by title.
  - `Book.cover_url` returns the Open Library medium cover URL when `cover_id`
    exists, otherwise an empty string.
- `library/models.py`
  - `UserBook` connecting the configured user model to `Book`.
  - Shelf statuses: `want`, `reading`, and `read`.
  - Optional rating, review, and automatic update time.
  - One user-book record is enforced with `unique_together`.
- `recommender/models.py`
  - `SimilarBook` connecting a source book to a similar target book.
  - Stores a score and model method, defaulting to `tfidf`.
  - Enforces uniqueness for `(book, similar_to, method)`.
  - Adds the `(book, method, -score)` database index.

Registered all models in Django admin:

- `books/admin.py`: `Author`, `Genre`, `Book`.
- `library/admin.py`: `UserBook`.
- `recommender/admin.py`: `SimilarBook`.

Generated migrations:

- `books/migrations/0001_initial.py`
- `library/migrations/0001_initial.py`
- `recommender/migrations/0001_initial.py`

## Step 2 validation record

Commands run successfully:

```powershell
.\venv\Scripts\python.exe manage.py makemigrations books library recommender
.\venv\Scripts\python.exe manage.py migrate --noinput
.\venv\Scripts\python.exe manage.py check
```

The migration command applied the initial migrations for `books`, `library`,
and `recommender`. Django's system check reported no issues.

An additional Django shell verification confirmed:

- The `Book` and `Genre` ordering metadata.
- Both `Book.cover_url` outcomes.
- All five models are registered in Django admin.
- The `SimilarBook` descending-score index exists.

Step 2 did not add views, templates, importing, authentication, or
recommendation behavior.

### Step 3 — Import books from Open Library

Status: **Completed and validated with the recommended small import.**

Created:

- `books/management/__init__.py`
- `books/management/commands/__init__.py`
- `books/management/commands/import_openlibrary.py`

The `import_openlibrary` management command:

- Accepts one or more Open Library subjects.
- Supports `--limit`, defaulting to 100 books per subject.
- Supports `--no-descriptions`.
- Creates or reuses a genre using a slugified subject.
- Requests subject data in pages of 50 with an offset.
- Creates books using the Open Library work key as `ol_key`.
- Saves title, cover ID, and first publication year.
- Creates or reuses authors and connects them to newly created books.
- Fetches descriptions only for newly created books unless
  `--no-descriptions` is supplied.
- Accepts descriptions returned as either strings or `{value: ...}` objects.
- Uses request timeouts and skips a description if its request fails.
- Waits 0.3 seconds between description requests.
- Always connects an imported or existing book to the subject genre.
- Prints the number of new books added for each subject.

The Open Library request `User-Agent` includes the contact email supplied by
the project owner:

```text
BookShelf/0.1 (vivesh61@outlook.com)
```

The API response was checked before implementation. The documented fields
`works`, `key`, `title`, `authors`, `cover_id`, and `first_publish_year` were
present in the response.

## Step 3 validation record

Commands run successfully:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py import_openlibrary fantasy --limit 50 --no-descriptions
```

Import result:

- `fantasy: 50 new books`
- Genres stored: 1
- Books stored: 50
- Authors stored: 23
- Fantasy books connected to the genre: 50

A database verification also confirmed that imported books have Open Library
work keys, authors, and cover URLs. No descriptions were requested in this
test because `--no-descriptions` was used.

The full multi-subject import from the instructions can be run later:

```powershell
.\venv\Scripts\python.exe manage.py import_openlibrary fantasy science_fiction mystery romance thriller horror historical_fiction --limit 150
```

That import may take approximately 15–20 minutes because description requests
are deliberately rate-limited.

Step 3 did not add pages, search, authentication, or recommendation behavior.

### Step 4 — Home, list, and detail pages

Status: **Completed and validated.**

Implemented public browsing pages using Django function-based views and plain
HTML, CSS, and JavaScript:

- `books/views.py`
  - `home`: latest covered books and top-rated books.
  - `book_list`: all books, optional genre filtering, rating annotations, and
    pagination of 24 books per page.
  - `book_detail`: authors, genres, rating statistics, reviews, current user's
    entry when authenticated, and up to eight TF-IDF similar books.
  - Shared rating annotation helper.
- `books/urls.py`
  - `/`
  - `/books/`
  - `/books/<id>/`
- `bookshelf/urls.py`
  - Includes the books URLs alongside `/admin/`.
- `templates/base.html`
  - Shared header, browse link, search form placeholder, authentication links,
    logout POST form, content block, and static JavaScript include.
- `templates/books/_card.html`
  - Cover, title, up to two authors, and average rating.
- `templates/books/home.html`
- `templates/books/book_list.html`
  - Genre chips and pagination links preserving the selected genre.
- `templates/books/book_detail.html`
  - Book information, description, ratings, reviews, and similar-books area.
  - Includes a placeholder for the Step 5 shelf form.
- `static/css/style.css`
  - Warm responsive layout, card grid, chips, detail layout, and review styles.
- `static/js/app.js`
  - Empty as required; interactive behavior is planned for Step 5.

Validation completed:

```powershell
.\venv\Scripts\python.exe manage.py check
```

The system check reported no issues. Django test-client requests to `/`,
`/books/`, `/books/?genre=fantasy`, and an imported book detail URL all
returned HTTP 200. The imported fantasy data makes the pages immediately
viewable.

Step 4 does not add search behavior, authentication, shelf forms, or review
submission. The search form is intentionally a placeholder for the later
search step.

### Rating display enhancement

Status: **Completed and validated.**

The public book cards and detail pages now show both rating sources:

- `Book.openlibrary_rating` and `Book.openlibrary_rating_count` store the
  external Open Library ratings.
- The existing `UserBook.rating` values are aggregated as the BookShelf
  average.
- Either source displays `Not rated yet` when no rating exists.

The Open Library importer now fetches each work's `/ratings.json` summary and
stores its average and count. Running the importer again also backfills
existing books whose external rating is still missing.

Created migration:

- `books/migrations/0002_book_openlibrary_rating_and_more.py`

Validation:

- Migration and Django system check passed.
- Existing fantasy books were refreshed with Open Library ratings.
- 49 of the 50 test-imported books currently have an Open Library rating;
  one has no external ratings available.
- The fantasy list page returned HTTP 200 and contains both rating labels.
- No BookShelf user ratings exist yet, so those entries correctly show
  `BookShelf: Not rated yet`.

The importer uses the Open Library ratings endpoint rather than guessing a
rating from unrelated book metadata.

Operational refresh performed after testing:

- `Le chat botté` had Open Library work key `/works/OL23867W`.
- Its exact Open Library ratings endpoint returned an average of `3.0` from
  `2` ratings.
- The earlier 50-book refresh had not reached this later fantasy result.
- Running `import_openlibrary fantasy --limit 150 --no-descriptions` stored the
  rating successfully.
- The detail page now renders `Open Library: 3.0` for this book.

The temporary Goodreads-style horizontal list presentation was reverted at the
user's request. The previous responsive card-grid layout is restored. The
Open Library and BookShelf rating displays remain unchanged.

### Step 5 — Accounts, shelves, ratings, and reviews

Status: **Completed and validated.**

Implemented:

- `library/views.py`
  - Signup using Django's `UserCreationForm`.
  - Login for new users after successful signup.
  - Authenticated POST-only shelf/rating/review saving.
  - Valid shelf status checking.
  - Ratings restricted to 1 through 5, with `0` clearing a rating.
  - Reviews trimmed and limited to 5,000 characters.
  - My-books view grouped by the three shelf statuses.
- `library/urls.py`
  - Signup, my-books, and save-entry routes.
- `bookshelf/urls.py`
  - Django built-in authentication URLs under `/accounts/`.
  - Library URL inclusion.
- `books/views.py`
  - Supplies shelf status choices and the current user's entry to the detail
    page.
- `templates/registration/login.html`
- `templates/registration/signup.html`
- `templates/library/_entry_form.html`
  - Shelf selector, clickable five-star rating widget, review field, and save
    button.
- `templates/library/my_books.html`
- `templates/books/book_detail.html`
  - Includes the shelf/rating/review form.
- `static/js/app.js`
  - Automatically submits shelf changes.
  - Supports star hover preview and click-to-save rating.
- `static/css/style.css`
  - Styles the entry form and star widget.

Validation completed:

```powershell
.\venv\Scripts\python.exe manage.py check
```

The system check reported no issues. Django test-client verification confirmed:

- Login page returns HTTP 200.
- Signup page returns HTTP 200.
- Book detail page returns HTTP 200.
- An authenticated user can save a shelf status, rating, and review.
- The save redirects back to the book detail page.
- The saved record appears through the my-books flow.

A temporary test account and its related database records were removed after
verification.

Step 5 did not add search or recommendations.

### Step 6 — PostgreSQL full-text search

Status: **Completed and validated.**

Implemented:

- `books/views.py`
  - A `search` function view reading and trimming `?q=`.
  - PostgreSQL `SearchVector` over title (weight A) and description (weight B).
  - `SearchQuery` using `search_type='websearch'`.
  - `SearchRank` ordering results by relevance, then title.
  - Author-name `icontains` fallback matching.
  - Distinct, prefetched results and pagination of 24 books per page.
- `books/urls.py`
  - Added the named `/search/` route.
- `templates/books/search.html`
  - Query heading, reusable book-card result grid, empty state, and pagination
    links preserving the search query.

The existing search form in `templates/base.html` now submits to a working
endpoint.

Validation completed:

```powershell
.\venv\Scripts\python.exe manage.py check
```

The system check reported no issues. Django test-client requests for an empty
search, a title word, an author word, a topic word, a quoted phrase, and a
second results page all returned HTTP 200. A title search also returned the
matching book content.

Step 6 did not add recommendations or change the fixed stack.

### Step 7 — TF-IDF recommender

Status: **Completed and validated.**

Implemented:

- `recommender/services.py`
  - Contains all scikit-learn and recommendation logic.
  - `book_text()` weights authors and genres by repeating them.
  - `build_tfidf_similarity()` uses the specified TF-IDF vectorizer and brute
    cosine nearest-neighbor search.
  - Deletes and rebuilds only `tfidf` similarity rows inside a transaction.
  - Skips self-links and non-positive similarity scores.
  - `recommend_for_user()` combines recommendations from books rated 4 or
    higher and excludes books already in the user's library.
- `recommender/management/__init__.py`
- `recommender/management/commands/__init__.py`
- `recommender/management/commands/build_recommendations.py`
  - Supports `--top-k`.
  - Prints the saved similarity-row count.
- `books/views.py`
  - Supplies recommendations to authenticated home-page users.
- `templates/books/home.html`
  - Displays a `Recommended for you` row when recommendations exist.

Step 7 build command:

```powershell
.\venv\Scripts\python.exe manage.py build_recommendations --top-k 10
```

Validation completed:

- `.\venv\Scripts\python.exe manage.py check` passed.
- The recommendation build saved `799` TF-IDF similarity rows for the current
  50-book catalog.
- A temporary user rated one book 5 stars and received 5 recommendation picks.
- The authenticated home page returned HTTP 200 and displayed
  `Recommended for you`.
- The temporary test user and related record were removed.

The recommender is ready to be rerun after importing more books. The command
should be scheduled nightly later if deployment requires automatic refreshes.

### Step 8 — Tests and deployment

Status: **Implemented. Deployment checks passed; automated tests are blocked by
PostgreSQL permissions.**

Added the requested core-flow tests to `books/tests.py`:

- Home, list, and detail pages return HTTP 200.
- Searching for `dune` returns the matching book.
- A logged-out save attempt redirects and creates no `UserBook`.
- A logged-in user can save shelf status, rating, and review.
- Recommendations include unseen similar books and skip books already in the
  user's library.

Deployment configuration:

- Installed `gunicorn` 26.2.0 and `whitenoise` 6.12.0.
- Recorded both packages in `requirements.txt`.
- Added WhiteNoise immediately after Django's security middleware.
- Added `STATIC_ROOT = BASE_DIR / 'staticfiles'`.
- Configured compressed manifest static-file storage through `STORAGES`.
- Added comma-separated `CSRF_TRUSTED_ORIGINS` environment parsing.
- `.env` now uses `DEBUG=False` for the deployment-oriented configuration.
- `DEBUG` already defaults to `False` when the environment variable is absent.

Validation completed:

- `.\venv\Scripts\python.exe manage.py check` passed.
- `.\venv\Scripts\python.exe manage.py collectstatic --noinput` passed;
  129 static files were copied and 387 were post-processed.
- Production settings verification passed for DEBUG, STATIC_ROOT, WhiteNoise
  middleware, and compressed manifest storage.

The test command was run:

```powershell
.\venv\Scripts\python.exe manage.py test books
```

Django discovered all 5 tests but could not create its temporary PostgreSQL
test database because the configured role lacks permission to create databases.
Grant `CREATEDB` to the PostgreSQL role, or run the tests using a dedicated
test-capable role, then rerun the command:

```sql
ALTER ROLE vivesh CREATEDB;
```

Do not grant this permission to a production role unless that is acceptable for
the deployment's security policy.

Deployment commands from the instructions:

```text
Build: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
Start: gunicorn bookshelf.wsgi
```

Required host environment variables:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

After deployment, load books with the Open Library command, run
`python manage.py build_recommendations`, and schedule that command nightly if
the hosting platform supports scheduled jobs.

## Important continuation rule

When a later step is completed, update this file rather than replacing it:

- Change the relevant step status.
- List files created or changed.
- Record validation commands and their outcomes.
- State any remaining environment blocker.
- Add the next step's exact scope and expected check.

This record is intentionally detailed so another AI can continue the project
safely without redoing Step 1 or accidentally starting a later step.
