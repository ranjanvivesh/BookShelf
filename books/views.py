import requests
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .management.commands.import_openlibrary import (
    HEADERS,
    fetch_description,
    fetch_ratings,
)
from library.models import UserBook
from recommender.models import SimilarBook
from recommender.services import recommend_for_user
from .models import Author, Book, Genre


OPEN_LIBRARY_SEARCH_URL = 'https://openlibrary.org/search.json'


def with_rating(queryset):
    return queryset.annotate(
        avg_rating=Avg('user_books__rating'),
        rating_count=Count('user_books__rating'),
    )


def home(request):
    latest = (
        with_rating(Book.objects.exclude(cover_id=None))
        .prefetch_related('authors')
        .order_by('-created_at')[:12]
    )
    top = (
        with_rating(Book.objects.prefetch_related('authors'))
        .filter(rating_count__gte=1)
        .order_by('-avg_rating', '-rating_count')[:12]
    )
    picks = recommend_for_user(request.user) if request.user.is_authenticated else []
    return render(request, 'books/home.html', {
        'latest': latest,
        'top': top,
        'picks': picks,
    })


def book_list(request):
    queryset = Book.objects.prefetch_related('authors').order_by('title')
    genre = None
    slug = request.GET.get('genre')
    if slug:
        genre = get_object_or_404(Genre, slug=slug)
        queryset = queryset.filter(genres=genre)

    page = Paginator(
        with_rating(queryset),
        24,
    ).get_page(request.GET.get('page'))
    return render(request, 'books/book_list.html', {
        'page': page,
        'genre': genre,
        'genres': Genre.objects.all(),
    })


def book_detail(request, pk):
    book = get_object_or_404(
        Book.objects.prefetch_related('authors', 'genres'),
        pk=pk,
    )
    stats = book.user_books.filter(rating__isnull=False).aggregate(
        avg=Avg('rating'),
        n=Count('id'),
    )
    reviews = (
        book.user_books.exclude(review='')
        .select_related('user')
        .order_by('-updated_at')
    )
    similar = (
        SimilarBook.objects.filter(book=book, method='tfidf')
        .select_related('similar_to')
        .order_by('-score')[:8]
    )
    entry = None
    if request.user.is_authenticated:
        entry = book.user_books.filter(user=request.user).first()

    return render(request, 'books/book_detail.html', {
        'book': book,
        'stats': stats,
        'reviews': reviews,
        'similar': similar,
        'entry': entry,
        'status_choices': UserBook.STATUS_CHOICES,
    })


def search(request):
    query_text = request.GET.get('q', '').strip()
    results = Book.objects.none()
    open_library_results = []
    open_library_error = ''
    if query_text:
        vector = (
            SearchVector('title', weight='A')
            + SearchVector('description', weight='B')
        )
        query = SearchQuery(query_text, search_type='websearch')
        results = (
            Book.objects.prefetch_related('authors')
            .annotate(rank=SearchRank(vector, query))
            .filter(
                Q(rank__gt=0)
                | Q(authors__name__icontains=query_text)
            )
            .distinct()
            .order_by('-rank', 'title')
        )
        try:
            response = requests.get(
                OPEN_LIBRARY_SEARCH_URL,
                headers=HEADERS,
                params={'q': query_text, 'limit': 12},
                timeout=20,
            )
            response.raise_for_status()
            open_library_results = [
                {
                    'key': item.get('key', ''),
                    'title': item.get('title', ''),
                    'authors': item.get('author_name', [])[:3],
                    'cover_id': item.get('cover_i'),
                    'published_year': item.get('first_publish_year'),
                    'edition_count': item.get('edition_count'),
                    'rating': item.get('ratings_average'),
                    'rating_count': item.get('ratings_count'),
                }
                for item in response.json().get('docs', [])
                if item.get('key') and item.get('title')
            ]
        except (requests.RequestException, ValueError):
            open_library_error = (
                'Open Library could not be reached. Local results are still shown.'
            )

    page = Paginator(results, 24).get_page(request.GET.get('page'))
    return render(request, 'books/search.html', {
        'q': query_text,
        'page': page,
        'open_library_results': open_library_results,
        'open_library_error': open_library_error,
    })


@require_POST
def import_open_library(request):
    work_key = request.POST.get('work_key', '').strip()
    if not work_key.startswith('/works/'):
        return render(request, 'books/search.html', {
            'q': '',
            'page': Paginator(Book.objects.none(), 24).get_page(None),
            'open_library_results': [],
            'open_library_error': 'The selected Open Library work is invalid.',
        }, status=400)

    try:
        response = requests.get(
            f'https://openlibrary.org{work_key}.json',
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        work = response.json()
    except (requests.RequestException, ValueError):
        return render(request, 'books/search.html', {
            'q': '',
            'page': Paginator(Book.objects.none(), 24).get_page(None),
            'open_library_results': [],
            'open_library_error': 'The Open Library book could not be imported.',
        }, status=502)

    book, created = Book.objects.get_or_create(
        ol_key=work_key,
        defaults={
            'title': work.get('title', '')[:500],
            'cover_id': (work.get('covers') or [None])[0],
            'description': fetch_description(work_key),
        },
    )
    if not book.title:
        return render(request, 'books/search.html', {
            'q': '',
            'page': Paginator(Book.objects.none(), 24).get_page(None),
            'open_library_results': [],
            'open_library_error': 'Open Library returned no usable title.',
        }, status=502)

    if created or book.openlibrary_rating is None:
        average, count = fetch_ratings(work_key)
        if average is not None:
            book.openlibrary_rating = average
            book.openlibrary_rating_count = count
            book.save(update_fields=['openlibrary_rating', 'openlibrary_rating_count'])

    for author_data in work.get('authors', []):
        author_key = author_data.get('author', {}).get('key', '')
        if not author_key:
            continue
        try:
            author_response = requests.get(
                f'https://openlibrary.org{author_key}.json',
                headers=HEADERS,
                timeout=15,
            )
            author_response.raise_for_status()
            author_name = author_response.json().get('name', '').strip()
        except (requests.RequestException, ValueError):
            continue
        if author_name:
            book.authors.add(Author.objects.get_or_create(name=author_name[:255])[0])

    return redirect('book_detail', pk=book.pk)
