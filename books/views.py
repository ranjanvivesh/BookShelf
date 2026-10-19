from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from library.models import UserBook
from recommender.models import SimilarBook
from recommender.services import recommend_for_user
from .models import Book, Genre


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

    page = Paginator(results, 24).get_page(request.GET.get('page'))
    return render(request, 'books/search.html', {
        'q': query_text,
        'page': page,
    })
