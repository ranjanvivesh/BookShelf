BookShelf: Step-by-Step Build Prompts
Oct 19, 2026 · @Vivesh
Overview
BookShelf is a small Goodreads-style site where people browse and search books, put them on shelves, rate and review them, and get recommendations from a TF-IDF model that runs offline. Each step below has a prompt to paste into your AI coding assistant, reference code showing what the result should look like, and a one-line check that it works.
Fixed stack
•	Backend: Django (function views only)
•	Database: PostgreSQL
•	Frontend: Django templates with plain HTML, CSS and JavaScript (no React, no npm)
•	ML: scikit-learn TF-IDF, precomputed nightly and stored in a table
•	Data: Open Library API for books and covers
Project structure
bookshelf/
  manage.py
  requirements.txt
  .env
  bookshelf/            # settings, root urls
  books/                # Author, Genre, Book; browse, detail, search; importer
  library/              # UserBook: shelf status, rating, review; signup
  recommender/          # SimilarBook table; services.py holds ALL ML code
  templates/            # base.html, books/, library/, registration/
  static/               # css/style.css, js/app.js
The room for future updates comes from three choices: the ML code lives in one file (recommender/services.py) so you can swap the model later, similar books are stored in a table with a method column so several models can coexist, and every step is a separate Django app or file, so nothing gets rewritten when you add features.
How to use the prompts
Start each new AI session by pasting the master prompt below, then paste one step prompt at a time and run its check before moving on.
You are helping me build BookShelf, a small Goodreads-style website.
Fixed stack, do not change it: Python 3.10+, Django 5, PostgreSQL (psycopg2), plain HTML/CSS/JavaScript in Django templates (no React, no CSS framework, no npm), scikit-learn + pandas for ML.
Rules: keep code short and readable; Django function views only; no REST API yet; no extra libraries beyond what I name; apps are books, library and recommender; ALL ML code lives in recommender/services.py so it can be swapped later.
For every file you create or change, show the full file. After the code, give me the exact command to run next and what I should see if it worked. Do not add features I did not ask for.
Step 1: Project setup and PostgreSQL
After this step, Django runs against an empty PostgreSQL database called bookshelf, with three empty apps ready.
Prompt to paste
Set up a new Django 5 project called bookshelf in the current folder, using a virtual environment.
Create three apps: books, library, recommender.
Configure settings.py to read SECRET_KEY, DEBUG, ALLOWED_HOSTS and the PostgreSQL credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT) from a .env file using python-dotenv.
Add django.contrib.postgres and the three apps to INSTALLED_APPS, point TEMPLATES DIRS at a top-level templates/ folder, and point STATICFILES_DIRS at a top-level static/ folder.
Set LOGIN_REDIRECT_URL and LOGOUT_REDIRECT_URL to '/'.
Give me: the terminal commands, the SQL to create the database, the .env file, a .gitignore (ignore .env and venv), and only the changed parts of settings.py.
Reference commands
python -m venv venv
source venv/bin/activate        # Windows: venv\\Scripts\\activate
pip install django psycopg2-binary python-dotenv pandas scikit-learn requests
django-admin startproject bookshelf .
python manage.py startapp books
python manage.py startapp library
python manage.py startapp recommender
pip freeze > requirements.txt
mkdir templates static

CREATE DATABASE bookshelf;

# .env
SECRET_KEY=change-me
DEBUG=True
DB_NAME=bookshelf
DB_USER=vivesh
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
Reference settings (changed parts only)
# bookshelf/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    # ...the default django.contrib apps stay...
    'django.contrib.postgres',
    'books',
    'library',
    'recommender',
]

# in TEMPLATES[0]:  'DIRS': [BASE_DIR / 'templates'],

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

STATICFILES_DIRS = [BASE_DIR / 'static']
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
Check: python manage.py migrate finishes without errors, and python manage.py runserver shows the Django welcome page.
Step 2: Database models
Three small model files cover the whole product: books, one row per user-book interaction, and the stored similar-book lists.
Prompt to paste
Create the Django models and admin registration.

books/models.py: Author (name, unique); Genre (name, slug unique, ordered by name); Book (title, authors M2M, genres M2M, description TextField blank, ol_key CharField unique and nullable for the Open Library work key, cover_id IntegerField nullable, published_year IntegerField nullable, created_at auto). Book is ordered by title and has a cover_url property that returns https://covers.openlibrary.org/b/id/{cover_id}-M.jpg or an empty string.

library/models.py: UserBook with user FK (related_name user_books), book FK (related_name user_books), status choices want/reading/read (default want), rating PositiveSmallIntegerField nullable (1 to 5), review TextField blank, updated_at auto. unique_together on (user, book).

recommender/models.py: SimilarBook with book FK (related_name similar_from), similar_to FK (related_name similar_to_set), score FloatField, method CharField default tfidf. unique_together on (book, similar_to, method) and an index on (book, method, -score).

Register every model in its app's admin.py. Then give me the makemigrations and migrate commands.
Reference code
# books/models.py
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=500)
    authors = models.ManyToManyField(Author, related_name='books', blank=True)
    genres = models.ManyToManyField(Genre, related_name='books', blank=True)
    description = models.TextField(blank=True)
    ol_key = models.CharField(max_length=30, unique=True, null=True, blank=True)
    cover_id = models.IntegerField(null=True, blank=True)
    published_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def cover_url(self):
        if self.cover_id:
            return f'https://covers.openlibrary.org/b/id/{self.cover_id}-M.jpg'
        return ''

# library/models.py
from django.conf import settings
from django.db import models
from books.models import Book


class UserBook(models.Model):
    WANT, READING, READ = 'want', 'reading', 'read'
    STATUS_CHOICES = [(WANT, 'Want to read'), (READING, 'Currently reading'), (READ, 'Read')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='user_books')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=WANT)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1 to 5
    review = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')

# recommender/models.py
from django.db import models
from books.models import Book


class SimilarBook(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='similar_from')
    similar_to = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='similar_to_set')
    score = models.FloatField()
    method = models.CharField(max_length=20, default='tfidf')  # lets several models coexist later

    class Meta:
        unique_together = ('book', 'similar_to', 'method')
        indexes = [models.Index(fields=['book', 'method', '-score'])]

# books/admin.py  (do the same in library/admin.py and recommender/admin.py)
from django.contrib import admin
from .models import Author, Genre, Book

admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)

python manage.py makemigrations books library recommender
python manage.py migrate
python manage.py createsuperuser
Check: log in at /admin/ and see Authors, Genres, Books, User books and Similar books listed.
Step 3: Import books from Open Library
A single management command pulls roughly 1,000 popular books across several genres, with authors, cover ids and descriptions, into your own database.
Prompt to paste
Write a Django management command books/management/commands/import_openlibrary.py (also create the two empty __init__.py files in management/ and management/commands/).
Usage: python manage.py import_openlibrary fantasy science_fiction mystery --limit 100 [--no-descriptions]
For each subject: get or create a Genre (slug from the subject, name title-cased with underscores replaced by spaces), then call https://openlibrary.org/subjects/<subject>.json with limit=50 and an offset, in pages until --limit books are reached.
For each work, get or create a Book keyed by ol_key (the work's key), saving title, cover_id and published_year (first_publish_year). For new books only: fetch the description from https://openlibrary.org<work key>.json (the description can be a string or a dict with a value key), save the authors, and sleep 0.3 seconds between description requests. Always add the subject's genre to the book.
Use the requests library with a User-Agent header that has a contact email, a timeout, and skip a book's description if its request fails instead of crashing.
Print how many new books were added per subject.
Reference code
# books/management/commands/import_openlibrary.py
import time

import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from books.models import Author, Genre, Book

BASE = 'https://openlibrary.org'
HEADERS = {'User-Agent': 'BookShelf/0.1 (you@example.com)'}  # use your real email
PAGE = 50


def fetch_description(work_key):
    try:
        r = requests.get(f'{BASE}{work_key}.json', headers=HEADERS, timeout=15)
        r.raise_for_status()
    except requests.RequestException:
        return ''
    desc = r.json().get('description', '')
    if isinstance(desc, dict):
        desc = desc.get('value', '')
    return desc or ''


class Command(BaseCommand):
    help = 'Import books from Open Library by subject, e.g. fantasy science_fiction'

    def add_arguments(self, parser):
        parser.add_argument('subjects', nargs='+')
        parser.add_argument('--limit', type=int, default=100, help='books per subject')
        parser.add_argument('--no-descriptions', action='store_true')

    def handle(self, *args, **opts):
        for subject in opts['subjects']:
            genre, _ = Genre.objects.get_or_create(
                slug=slugify(subject),
                defaults={'name': subject.replace('_', ' ').title()},
            )
            added = 0
            for offset in range(0, opts['limit'], PAGE):
                r = requests.get(
                    f'{BASE}/subjects/{subject}.json',
                    headers=HEADERS, timeout=30,
                    params={'limit': PAGE, 'offset': offset},
                )
                r.raise_for_status()
                works = r.json().get('works', [])
                if not works:
                    break
                for w in works:
                    book, created = Book.objects.get_or_create(
                        ol_key=w['key'],
                        defaults={
                            'title': w['title'][:500],
                            'cover_id': w.get('cover_id'),
                            'published_year': w.get('first_publish_year'),
                        },
                    )
                    if created:
                        added += 1
                        if not opts['no_descriptions']:
                            book.description = fetch_description(w['key'])
                            book.save(update_fields=['description'])
                            time.sleep(0.3)
                        for a in w.get('authors', []):
                            author, _ = Author.objects.get_or_create(name=a['name'][:255])
                            book.authors.add(author)
                    book.genres.add(genre)
            self.stdout.write(f'{subject}: {added} new books')

# quick test first (no descriptions, fast)
python manage.py import_openlibrary fantasy --limit 50 --no-descriptions

# real import: about 1,000 books, roughly 15 to 20 minutes with descriptions
python manage.py import_openlibrary fantasy science_fiction mystery romance thriller horror historical_fiction --limit 150
Before the first run, open https://openlibrary.org/subjects/fantasy.json?limit=2 in a browser and confirm the fields (works, key, title, authors, cover_id, first_publish_year) still look like this, since third-party APIs can change. Many works have no description, which is fine: the recommender in Step 7 also uses genres and authors.
Check: the admin shows hundreds of books, and https://covers.openlibrary.org/b/id/<a cover_id from a book>-M.jpg opens a cover image.
Step 4: Home, list and detail pages
This step gives you a working site you can click through: a home page, a paginated book list with genre filters, and a book page with similar books and reviews.
Prompt to paste
Build the public pages for BookShelf using Django function views and plain HTML/CSS. No JavaScript yet (just create an empty static/js/app.js).

books/views.py:
- home: 12 latest books that have a cover, and 12 top-rated books (average of UserBook.rating, only books with at least 1 rating). Use a small helper that annotates avg_rating and rating_count.
- book_list: all books, optional ?genre=<slug> filter, annotated with ratings, paginated 24 per page.
- book_detail: the book with its authors and genres, rating average and count, reviews (UserBook rows with a non-empty review, newest first), the user's own UserBook if logged in, and up to 8 SimilarBook rows (method tfidf, highest score first).
books/urls.py with names home, book_list, book_detail; include it from bookshelf/urls.py along with admin.

Templates in templates/: base.html (header with brand, a search form that GETs /search/, and login/signup or my books/logout links using literal URLs /accounts/login/, /accounts/signup/, /my-books/; a logout POST form to /accounts/logout/ with csrf_token; a content block; a script tag for static/js/app.js), books/_card.html (cover, title, up to 2 authors, average rating), books/home.html, books/book_list.html (genre chips and Previous/Next links that keep the genre), books/book_detail.html (cover, title, authors, genre chips, rating, description, a placeholder comment where the shelf form will go later, a Readers also liked grid, and reviews).
static/css/style.css: simple warm style, responsive card grid, no framework.
Reference code
# books/views.py
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.shortcuts import render, get_object_or_404

from recommender.models import SimilarBook
from .models import Book, Genre


def with_rating(qs):
    return qs.annotate(avg_rating=Avg('user_books__rating'),
                       rating_count=Count('user_books__rating'))


def home(request):
    latest = Book.objects.exclude(cover_id=None).prefetch_related('authors').order_by('-created_at')[:12]
    top = (with_rating(Book.objects.prefetch_related('authors'))
           .filter(rating_count__gte=1).order_by('-avg_rating', '-rating_count')[:12])
    return render(request, 'books/home.html', {'latest': latest, 'top': top})


def book_list(request):
    qs = Book.objects.prefetch_related('authors')
    genre = None
    slug = request.GET.get('genre')
    if slug:
        genre = get_object_or_404(Genre, slug=slug)
        qs = qs.filter(genres=genre)
    page = Paginator(with_rating(qs), 24).get_page(request.GET.get('page'))
    return render(request, 'books/book_list.html',
                  {'page': page, 'genre': genre, 'genres': Genre.objects.all()})


def book_detail(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related('authors', 'genres'), pk=pk)
    stats = book.user_books.filter(rating__isnull=False).aggregate(avg=Avg('rating'), n=Count('id'))
    reviews = book.user_books.exclude(review='').select_related('user').order_by('-updated_at')
    similar = (SimilarBook.objects.filter(book=book, method='tfidf')
               .select_related('similar_to').order_by('-score')[:8])
    entry = None
    if request.user.is_authenticated:
        entry = book.user_books.filter(user=request.user).first()
    return render(request, 'books/book_detail.html', {
        'book': book, 'stats': stats, 'reviews': reviews, 'similar': similar, 'entry': entry})

# books/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
]

# bookshelf/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('books.urls')),
]

<!-- templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>{% block title %}BookShelf{% endblock %}</title>
  <link rel='stylesheet' href='{% static 'css/style.css' %}'>
</head>
<body>
<header>
  <div class='bar'>
    <a class='brand' href='/'>BookShelf</a>
    <a href='/books/'>Browse</a>
    <form class='search' action='/search/' method='get'>
      <input type='search' name='q' placeholder='Search title, author or topic' value='{{ q|default:'' }}'>
      <button type='submit'>Search</button>
    </form>
    {% if user.is_authenticated %}
      <a href='/my-books/'>My books</a>
      <form action='/accounts/logout/' method='post'>{% csrf_token %}<button type='submit'>Log out</button></form>
    {% else %}
      <a href='/accounts/login/'>Log in</a>
      <a href='/accounts/signup/'>Sign up</a>
    {% endif %}
  </div>
</header>
<main>{% block content %}{% endblock %}</main>
<script src='{% static 'js/app.js' %}' defer></script>
</body>
</html>

<!-- templates/books/_card.html -->
<a class='card' href='{% url 'book_detail' book.pk %}'>
  {% if book.cover_url %}<img src='{{ book.cover_url }}' alt='' loading='lazy'>{% else %}<div class='nocover'>No cover</div>{% endif %}
  <div class='card-title'>{{ book.title }}</div>
  <div class='card-sub'>{% for a in book.authors.all|slice:':2' %}{{ a.name }}{% if not forloop.last %}, {% endif %}{% endfor %}</div>
  {% if book.avg_rating %}<div class='card-sub'>&#9733; {{ book.avg_rating|floatformat:1 }}</div>{% endif %}
</a>

<!-- templates/books/home.html -->
{% extends 'base.html' %}
{% block content %}
{% if top %}
  <h2>Top rated</h2>
  <div class='grid'>{% for book in top %}{% include 'books/_card.html' %}{% endfor %}</div>
{% endif %}
<h2>New on the shelf</h2>
<div class='grid'>{% for book in latest %}{% include 'books/_card.html' %}{% endfor %}</div>
{% endblock %}

<!-- templates/books/book_list.html -->
{% extends 'base.html' %}
{% block title %}Browse books{% endblock %}
{% block content %}
<h2>{% if genre %}{{ genre.name }}{% else %}All books{% endif %}</h2>
<div class='chips'>
  <a href='{% url 'book_list' %}'>All</a>
  {% for g in genres %}<a href='?genre={{ g.slug }}'>{{ g.name }}</a>{% endfor %}
</div>
<div class='grid'>{% for book in page %}{% include 'books/_card.html' %}{% endfor %}</div>
<div class='pager'>
  {% if page.has_previous %}<a href='?page={{ page.previous_page_number }}{% if genre %}&genre={{ genre.slug }}{% endif %}'>Previous</a>{% endif %}
  <span class='muted'>Page {{ page.number }} of {{ page.paginator.num_pages }}</span>
  {% if page.has_next %}<a href='?page={{ page.next_page_number }}{% if genre %}&genre={{ genre.slug }}{% endif %}'>Next</a>{% endif %}
</div>
{% endblock %}

<!-- templates/books/book_detail.html -->
{% extends 'base.html' %}
{% block title %}{{ book.title }}{% endblock %}
{% block content %}
<div class='detail'>
  <div>{% if book.cover_url %}<img src='{{ book.cover_url }}' alt='Cover of {{ book.title }}'>{% endif %}</div>
  <div class='info'>
    <h1>{{ book.title }}</h1>
    <p>by {% for a in book.authors.all %}{{ a.name }}{% if not forloop.last %}, {% endif %}{% endfor %}</p>
    <div class='chips'>{% for g in book.genres.all %}<a href='{% url 'book_list' %}?genre={{ g.slug }}'>{{ g.name }}</a>{% endfor %}</div>
    {% if stats.n %}<p>&#9733; {{ stats.avg|floatformat:1 }} from {{ stats.n }} rating{{ stats.n|pluralize }}</p>{% else %}<p class='muted'>No ratings yet</p>{% endif %}
    <p>{{ book.description|linebreaksbr|default:'No description available.' }}</p>
    <!-- Step 5: shelf, rating and review form goes here -->
  </div>
</div>

<h2>Readers also liked</h2>
{% if similar %}
  <div class='grid'>{% for s in similar %}{% include 'books/_card.html' with book=s.similar_to %}{% endfor %}</div>
{% else %}
  <p class='muted'>No recommendations yet.</p>
{% endif %}

<h2>Reviews</h2>
{% for r in reviews %}
  <div class='review'><strong>{{ r.user.username }}</strong>{% if r.rating %} &#9733; {{ r.rating }}{% endif %}<p>{{ r.review|linebreaksbr }}</p></div>
{% empty %}
  <p class='muted'>No reviews yet.</p>
{% endfor %}
{% endblock %}

/* static/css/style.css */
:root { --bg: #faf7f2; --ink: #2b2b2b; --accent: #7a4e2d; --muted: #777; --line: #e6dfd3; }
* { box-sizing: border-box; }
body { margin: 0; font-family: Georgia, serif; background: var(--bg); color: var(--ink); line-height: 1.5; }
a { color: var(--accent); text-decoration: none; }
header { background: #fff; border-bottom: 1px solid var(--line); }
.bar, main { max-width: 1000px; margin: 0 auto; padding: 12px 16px; }
.bar { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.brand { font-size: 1.4rem; font-weight: bold; }
.bar .search { flex: 1; display: flex; gap: 6px; min-width: 220px; }
.bar input[type=search] { flex: 1; padding: 6px 10px; border: 1px solid var(--line); border-radius: 6px; }
button, .btn { background: var(--accent); color: #fff; border: 0; border-radius: 6px; padding: 7px 14px; cursor: pointer; font: inherit; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 16px; }
.card { display: block; color: inherit; }
.card img, .nocover { width: 100%; aspect-ratio: 2 / 3; object-fit: cover; border-radius: 6px; background: #e8e1d6; }
.nocover { display: flex; align-items: center; justify-content: center; color: var(--muted); }
.card-title { font-weight: bold; margin-top: 6px; font-size: .95rem; }
.card-sub, .muted { color: var(--muted); font-size: .85rem; }
.chips a { display: inline-block; padding: 3px 10px; margin: 0 6px 6px 0; border: 1px solid var(--line); border-radius: 99px; background: #fff; font-size: .85rem; }
.detail { display: flex; gap: 24px; flex-wrap: wrap; }
.detail img { width: 220px; border-radius: 6px; }
.detail .info { flex: 1; min-width: 260px; }
.review { border-top: 1px solid var(--line); padding: 10px 0; }
.pager { margin: 20px 0; display: flex; gap: 12px; align-items: center; }

mkdir -p static/css static/js templates/books
touch static/js/app.js
Check: python manage.py runserver, then open /, /books/, click a genre chip, and open a book. The Readers also liked area says no recommendations yet, which is expected until Step 7.
Step 5: Accounts, shelves, ratings and reviews
Users can sign up, put a book on a shelf, rate it with clickable stars and write a review, all through one plain HTML form and a small amount of JavaScript.
Prompt to paste
Add user accounts and the library features.

1. Use Django's built-in auth views via include('django.contrib.auth.urls') under accounts/. Add a signup view using UserCreationForm that logs the user in and redirects home. Create templates registration/login.html and registration/signup.html extending base.html. Note that Django 5 logout only accepts POST, which base.html already does.
2. library/views.py: save_entry (login required, POST only) that gets or creates the UserBook for the current user and book, updates status only if it is one of the valid choices, updates rating only if it is a digit from 1 to 5 (the value 0 clears it), updates review (trimmed, max 5000 characters) only if it was sent, saves, then redirects to the book page. my_books (login required) that shows the user's books grouped by the three shelves.
3. library/urls.py with names signup, my_books, save_entry (library/save/<book_id>/), included from the root urls.
4. templates/library/_entry_form.html: a form with a status select (auto-submits on change), five clickable stars that fill a hidden rating input and submit the form, a review textarea and a Save button; logged-out users see a log in link instead. Include it in book_detail.html in place of the placeholder comment, and pass status_choices from the book_detail view.
5. templates/library/my_books.html using the existing book card.
6. static/js/app.js: vanilla JavaScript for the select auto-submit and the star widget (hover preview, click to set). Add the small CSS needed.
Reference code
# library/views.py
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from books.models import Book
from .models import UserBook


def signup(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        return redirect('home')
    return render(request, 'registration/signup.html', {'form': form})


@login_required
@require_POST
def save_entry(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    entry, _ = UserBook.objects.get_or_create(user=request.user, book=book)

    status = request.POST.get('status')
    if status in dict(UserBook.STATUS_CHOICES):
        entry.status = status

    rating = request.POST.get('rating', '')
    if rating == '0':
        entry.rating = None
    elif rating.isdigit() and 1 <= int(rating) <= 5:
        entry.rating = int(rating)

    if 'review' in request.POST:
        entry.review = request.POST['review'].strip()[:5000]

    entry.save()
    return redirect('book_detail', pk=book.pk)


@login_required
def my_books(request):
    entries = request.user.user_books.select_related('book').prefetch_related('book__authors')
    shelves = [(label, entries.filter(status=value)) for value, label in UserBook.STATUS_CHOICES]
    return render(request, 'library/my_books.html', {'shelves': shelves})

# library/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('accounts/signup/', views.signup, name='signup'),
    path('my-books/', views.my_books, name='my_books'),
    path('library/save/<int:book_id>/', views.save_entry, name='save_entry'),
]

# bookshelf/urls.py  (add these two lines inside urlpatterns)
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('library.urls')),

# books/views.py  (changes in book_detail only)
from library.models import UserBook          # new import at the top

# ...and add this key to the context dict that book_detail passes to render():
#     'status_choices': UserBook.STATUS_CHOICES,

<!-- templates/registration/login.html -->
{% extends 'base.html' %}
{% block title %}Log in{% endblock %}
{% block content %}
<h2>Log in</h2>
<form method='post'>{% csrf_token %}{{ form.as_p }}<button type='submit'>Log in</button></form>
<p class='muted'>New here? <a href='/accounts/signup/'>Create an account</a></p>
{% endblock %}

<!-- templates/registration/signup.html: same layout, heading Sign up, button Create account -->

<!-- templates/library/_entry_form.html -->
{% if user.is_authenticated %}
<form class='entry' method='post' action='{% url 'save_entry' book.pk %}'>
  {% csrf_token %}
  <select name='status' data-autosubmit>
    {% for value, label in status_choices %}
      <option value='{{ value }}' {% if entry and entry.status == value %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>
  <div class='stars' data-value='{{ entry.rating|default:0 }}'>
    {% for i in '12345' %}<span data-n='{{ i }}'>&#9733;</span>{% endfor %}
  </div>
  <input type='hidden' name='rating' value='{{ entry.rating|default:'' }}'>
  <textarea name='review' rows='4' placeholder='Write a review (optional)'>{{ entry.review }}</textarea>
  <button type='submit'>Save</button>
</form>
{% else %}
<p class='muted'><a href='/accounts/login/'>Log in</a> to shelve, rate and review this book.</p>
{% endif %}

<!-- in books/book_detail.html, replace the Step 5 comment with: -->
{% include 'library/_entry_form.html' %}

<!-- templates/library/my_books.html -->
{% extends 'base.html' %}
{% block title %}My books{% endblock %}
{% block content %}
<h1>My books</h1>
{% for label, entries in shelves %}
  <h2>{{ label }} ({{ entries|length }})</h2>
  <div class='grid'>
    {% for e in entries %}{% include 'books/_card.html' with book=e.book %}{% endfor %}
  </div>
{% endfor %}
{% endblock %}

// static/js/app.js
document.querySelectorAll('select[data-autosubmit]').forEach(function (sel) {
  sel.addEventListener('change', function () { sel.form.submit(); });
});

document.querySelectorAll('.stars').forEach(function (box) {
  var input = box.parentElement.querySelector('input[name=rating]');
  var stars = box.querySelectorAll('span');

  function paint(value) {
    stars.forEach(function (s) {
      s.classList.toggle('on', Number(s.dataset.n) <= value);
    });
  }

  paint(Number(box.dataset.value));
  box.addEventListener('mouseleave', function () { paint(Number(box.dataset.value)); });
  stars.forEach(function (s) {
    s.addEventListener('mouseover', function () { paint(Number(s.dataset.n)); });
    s.addEventListener('click', function () {
      input.value = s.dataset.n;
      box.dataset.value = s.dataset.n;
      input.form.submit();
    });
  });
});

/* append to static/css/style.css */
.entry { margin: 16px 0; display: grid; gap: 10px; max-width: 460px; }
.entry textarea, .entry select { padding: 8px; border: 1px solid var(--line); border-radius: 6px; font: inherit; }
.stars span { cursor: pointer; font-size: 1.8rem; color: #ccc; }
.stars span.on { color: #e0a100; }
Check: sign up, open a book, pick a shelf, click four stars, write a review and save. The page reloads with your rating, /my-books/ lists the book under the right shelf, and the home page now shows a Top rated row.
Step 6: Search
PostgreSQL's built-in full-text search handles titles, descriptions and author names, so you need no extra search service.
Prompt to paste
Add search to the books app using PostgreSQL full-text search from django.contrib.postgres.search.
View search(request): read ?q=, build a SearchVector over title (weight A) and description (weight B), use SearchQuery with search_type='websearch', annotate SearchRank, and return books whose rank is above 0 OR whose author name contains the query (icontains). Use distinct(), order by rank descending then title, and paginate 24 per page.
Add the URL path search/ named search, and a template books/search.html that shows the query, a result grid using the existing card, a no-results message, and Previous/Next links that keep q. The search box in base.html already submits to /search/.
Reference code
# books/views.py  (add these imports at the top, and this view at the bottom)
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q


def search(request):
    q = request.GET.get('q', '').strip()
    results = Book.objects.none()
    if q:
        vector = SearchVector('title', weight='A') + SearchVector('description', weight='B')
        query = SearchQuery(q, search_type='websearch')
        results = (Book.objects.prefetch_related('authors')
                   .annotate(rank=SearchRank(vector, query))
                   .filter(Q(rank__gt=0) | Q(authors__name__icontains=q))
                   .distinct()
                   .order_by('-rank', 'title'))
    page = Paginator(results, 24).get_page(request.GET.get('page'))
    return render(request, 'books/search.html', {'q': q, 'page': page})

# books/urls.py  (add inside urlpatterns)
    path('search/', views.search, name='search'),

<!-- templates/books/search.html -->
{% extends 'base.html' %}
{% block title %}Search{% endblock %}
{% block content %}
{% if q %}
  <h2>Results for '{{ q }}'</h2>
  <div class='grid'>
    {% for book in page %}{% include 'books/_card.html' %}
    {% empty %}<p class='muted'>No books matched. Try a shorter query or an author name.</p>{% endfor %}
  </div>
  <div class='pager'>
    {% if page.has_previous %}<a href='?q={{ q|urlencode }}&page={{ page.previous_page_number }}'>Previous</a>{% endif %}
    {% if page.has_next %}<a href='?q={{ q|urlencode }}&page={{ page.next_page_number }}'>Next</a>{% endif %}
  </div>
{% else %}
  <p class='muted'>Type a title, author or topic in the search box.</p>
{% endif %}
{% endblock %}
Check: search for an author surname, a title word and a topic word like dragon. Quoted phrases and a leading minus (to exclude a word) also work because of the websearch mode.
Step 7: ML recommender (TF-IDF)
A command turns each book's title, authors, genres and description into TF-IDF vectors, finds the 10 nearest books by cosine similarity, and saves them in the SimilarBook table, so the website only does a fast database lookup and never runs a model per request.
Prompt to paste
Implement the recommender. Put ALL ML code in recommender/services.py and keep the rest of the app free of scikit-learn imports.

1. book_text(book): title, then authors twice, then genres twice, then description (repeating authors and genres gives them more weight).
2. build_tfidf_similarity(top_k=10): load all books with prefetch_related, return 0 if there are fewer than 20 books, fit a TfidfVectorizer (english stop words, ngram_range (1,2), min_df=2, max_df=0.8, max_features=50000), use NearestNeighbors(metric='cosine', algorithm='brute') with top_k+1 neighbors, skip the book itself and any score of 0 or less, and in one transaction delete all SimilarBook rows with method 'tfidf' and bulk_create the new ones. Return the number of rows saved.
3. recommend_for_user(user, limit=12): take the books the user rated 4 or higher, collect their SimilarBook rows (method tfidf), exclude every book already in the user's library, sum the scores per candidate book, and return the top books in order.
4. A management command build_recommendations (with the two empty __init__.py files) that calls build_tfidf_similarity and prints the row count; it will run nightly from cron.
5. Update the home view to pass picks = recommend_for_user(request.user) for logged-in users, and show a Recommended for you row at the top of home.html when picks is not empty.
Reference code
# recommender/services.py
"""All ML code lives here. To change the model later, change only this file."""
from django.db import transaction
from django.db.models import Sum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from books.models import Book
from library.models import UserBook
from .models import SimilarBook

TOP_K = 10


def book_text(book):
    authors = ' '.join(a.name for a in book.authors.all())
    genres = ' '.join(g.name for g in book.genres.all())
    return f'{book.title} {authors} {authors} {genres} {genres} {book.description}'


def build_tfidf_similarity(top_k=TOP_K):
    books = list(Book.objects.prefetch_related('authors', 'genres'))
    if len(books) < 20:
        return 0

    texts = [book_text(b) for b in books]
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2),
                                 min_df=2, max_df=0.8, max_features=50000)
    matrix = vectorizer.fit_transform(texts)

    nn = NearestNeighbors(n_neighbors=min(top_k + 1, len(books)),
                          metric='cosine', algorithm='brute')
    nn.fit(matrix)
    distances, indices = nn.kneighbors(matrix)

    rows = []
    for i, book in enumerate(books):
        kept = 0
        for dist, j in zip(distances[i], indices[i]):
            if j == i or kept >= top_k:
                continue
            score = 1 - dist
            if score <= 0:
                continue
            rows.append(SimilarBook(book=book, similar_to=books[j],
                                    score=float(score), method='tfidf'))
            kept += 1

    with transaction.atomic():
        SimilarBook.objects.filter(method='tfidf').delete()
        SimilarBook.objects.bulk_create(rows, batch_size=1000)
    return len(rows)


def recommend_for_user(user, limit=12):
    liked = UserBook.objects.filter(user=user, rating__gte=4).values_list('book_id', flat=True)
    seen = UserBook.objects.filter(user=user).values_list('book_id', flat=True)
    rows = (SimilarBook.objects.filter(book_id__in=liked, method='tfidf')
            .exclude(similar_to_id__in=seen)
            .values('similar_to_id')
            .annotate(total=Sum('score'))
            .order_by('-total')[:limit])
    ids = [r['similar_to_id'] for r in rows]
    by_id = Book.objects.prefetch_related('authors').in_bulk(ids)
    return [by_id[i] for i in ids if i in by_id]

# recommender/management/commands/build_recommendations.py
from django.core.management.base import BaseCommand
from recommender.services import build_tfidf_similarity


class Command(BaseCommand):
    help = 'Recompute similar-book lists (run nightly with cron)'

    def add_arguments(self, parser):
        parser.add_argument('--top-k', type=int, default=10)

    def handle(self, *args, **opts):
        n = build_tfidf_similarity(top_k=opts['top_k'])
        self.stdout.write(f'Saved {n} similarity rows')

# books/views.py  (home view, updated)
from recommender.services import recommend_for_user   # new import at the top


def home(request):
    latest = Book.objects.exclude(cover_id=None).prefetch_related('authors').order_by('-created_at')[:12]
    top = (with_rating(Book.objects.prefetch_related('authors'))
           .filter(rating_count__gte=1).order_by('-avg_rating', '-rating_count')[:12])
    picks = recommend_for_user(request.user) if request.user.is_authenticated else []
    return render(request, 'books/home.html', {'latest': latest, 'top': top, 'picks': picks})

<!-- templates/books/home.html: add at the top of the content block -->
{% if picks %}
  <h2>Recommended for you</h2>
  <div class='grid'>{% for book in picks %}{% include 'books/_card.html' %}{% endfor %}</div>
{% endif %}

mkdir -p recommender/management/commands
touch recommender/management/__init__.py recommender/management/commands/__init__.py
python manage.py build_recommendations

# nightly at 3 am (crontab -e), adjust the paths
0 3 * * * cd /path/to/bookshelf && venv/bin/python manage.py build_recommendations
Check: run python manage.py shell and print the neighbors of a book you know:
from books.models import Book
b = Book.objects.filter(title__icontains='hobbit').first()   # any title you imported
for s in b.similar_from.order_by('-score')[:5]:
    print(round(s.score, 2), s.similar_to.title)
The neighbors should share a genre, author or theme. Then rate a few books 4 or 5 stars as a user, reload the home page, and a Recommended for you row appears.
What this model can and cannot do. TF-IDF finds books that use similar words, genres and authors. It does not learn from what other readers did, and a new user with no 4-star ratings sees no personal picks yet. Collaborative filtering (see Future updates) is the natural next model, and it fits in because results are stored with a method column.
Step 8: Tests and deployment
Five short tests protect the core flows, and a few settings changes make the same code run on a real host with Gunicorn and WhiteNoise.
Prompt to paste (tests)
Write books/tests.py using Django's TestCase with these tests: home, book list and book detail pages return 200; search for 'dune' returns the matching book; save_entry redirects and creates nothing when logged out; save_entry saves status, rating and review for a logged-in user; recommend_for_user returns a similar book the user has not seen and skips books already in their library. Keep it short and tell me the command to run the tests.

# books/tests.py
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from books.models import Book
from library.models import UserBook
from recommender.models import SimilarBook
from recommender.services import recommend_for_user


class BookShelfTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ann', password='pw12345!')
        self.book = Book.objects.create(title='Dune', description='desert planet spice')
        self.other = Book.objects.create(title='Children of Dune', description='desert planet sequel')

    def test_pages_load(self):
        for name in ('home', 'book_list'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        r = self.client.get(reverse('book_detail', args=[self.book.pk]))
        self.assertEqual(r.status_code, 200)

    def test_search_finds_title(self):
        r = self.client.get(reverse('search'), {'q': 'dune'})
        self.assertContains(r, 'Dune')

    def test_save_entry_requires_login(self):
        r = self.client.post(reverse('save_entry', args=[self.book.pk]), {'rating': '5'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(UserBook.objects.count(), 0)

    def test_save_rating_and_review(self):
        self.client.login(username='ann', password='pw12345!')
        self.client.post(reverse('save_entry', args=[self.book.pk]),
                         {'status': 'read', 'rating': '5', 'review': 'Great'})
        e = UserBook.objects.get(user=self.user, book=self.book)
        self.assertEqual((e.status, e.rating, e.review), ('read', 5, 'Great'))

    def test_recommendations_skip_seen_books(self):
        UserBook.objects.create(user=self.user, book=self.book, status='read', rating=5)
        SimilarBook.objects.create(book=self.book, similar_to=self.other, score=0.8)
        self.assertEqual(recommend_for_user(self.user), [self.other])

python manage.py test
Django builds a temporary test database, so your PostgreSQL user needs permission to create databases.
Prompt to paste (deployment)
Prepare BookShelf for deployment on a host with managed PostgreSQL. Add gunicorn and whitenoise to requirements.txt. In settings.py: add WhiteNoiseMiddleware right after SecurityMiddleware, set STATIC_ROOT to staticfiles, use the WhiteNoise compressed manifest storage through the STORAGES setting, and read CSRF_TRUSTED_ORIGINS from an environment variable. Make sure DEBUG defaults to False. Give me the build command, the start command, and the list of environment variables to set on the host.

# bookshelf/settings.py (changes)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # right after SecurityMiddleware
    # ...the rest stays as it is...
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o]

pip install gunicorn whitenoise
pip freeze > requirements.txt
Setting on the host	Value
Build command	pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
Start command	gunicorn bookshelf.wsgi
Environment variables	SECRET_KEY, DEBUG=False, ALLOWED_HOSTS (your domain), CSRF_TRUSTED_ORIGINS (https://your-domain), DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
First data load	Run python manage.py import_openlibrary ... and then build_recommendations once from the host's shell
Nightly job	python manage.py build_recommendations as a scheduled job; if your plan has none, run it by hand after each import
Check: python manage.py test passes locally, and after deploying you can sign up, rate a book and see similar books on its page.
Future updates
Each upgrade below plugs into an existing place, so none of them needs a rewrite: new models write into SimilarBook under a new method value, new fields arrive as Django migrations, and everything else stays in its own app.
Upgrade	Where it plugs in	What changes
Better text model (sentence embeddings)	recommender/services.py	Add build_embedding_similarity() that saves rows with method='embed', install sentence-transformers, then switch the method filter in book_detail
Collaborative filtering (readers who liked this also liked)	recommender/services.py	Build item-item similarity from the UserBook rating matrix, save as method='cf', and blend scores in recommend_for_user. Needs real user ratings first
Faster, smarter search	books app	Add a SearchVectorField with a GIN index, or trigram matching for typos
Review sentiment	library app	Add a sentiment field to UserBook, fill it with VADER when a review is saved, show a summary on the book page
Bigger catalog	books management commands	Add a second importer that reads Open Library's monthly dumps and filters to popular books
Caching	settings and views	Turn on Django's cache for the home and detail pages
Background jobs	recommender	Keep cron while jobs are short; move to a task queue only if they grow
Follows and activity feed	library app	Add a Follow model and a feed view built from recent UserBook rows
JSON API or separate frontend	new api app	Add Django REST Framework next to the current views; the templates keep working
Measuring recommendation quality	recommender	Hold out some ratings and report precision at K for each method before switching models
A sensible order is tests first, then measuring quality, then collaborative filtering once you have real ratings, then embeddings only if the measured results justify the extra weight.
