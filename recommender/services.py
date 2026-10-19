"""All ML code lives here so the recommendation model can be replaced later."""

from django.db import transaction
from django.db.models import Sum
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from books.models import Book
from library.models import UserBook
from .models import SimilarBook


TOP_K = 10


def book_text(book):
    authors = ' '.join(author.name for author in book.authors.all())
    genres = ' '.join(genre.name for genre in book.genres.all())
    return f'{book.title} {authors} {authors} {genres} {genres} {book.description}'


def build_tfidf_similarity(top_k=TOP_K):
    books = list(Book.objects.prefetch_related('authors', 'genres'))
    if len(books) < 20:
        return 0

    texts = [book_text(book) for book in books]
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.8,
        max_features=50000,
    )
    matrix = vectorizer.fit_transform(texts)
    neighbors = NearestNeighbors(
        n_neighbors=min(top_k + 1, len(books)),
        metric='cosine',
        algorithm='brute',
    )
    neighbors.fit(matrix)
    distances, indices = neighbors.kneighbors(matrix)

    rows = []
    for index, book in enumerate(books):
        kept = 0
        for distance, similar_index in zip(distances[index], indices[index]):
            if similar_index == index or kept >= top_k:
                continue
            score = 1 - distance
            if score <= 0:
                continue
            rows.append(SimilarBook(
                book=book,
                similar_to=books[similar_index],
                score=float(score),
                method='tfidf',
            ))
            kept += 1

    with transaction.atomic():
        SimilarBook.objects.filter(method='tfidf').delete()
        SimilarBook.objects.bulk_create(rows, batch_size=1000)
    return len(rows)


def recommend_for_user(user, limit=12):
    liked = UserBook.objects.filter(
        user=user,
        rating__gte=4,
    ).values_list('book_id', flat=True)
    seen = UserBook.objects.filter(user=user).values_list('book_id', flat=True)
    rows = (
        SimilarBook.objects.filter(book_id__in=liked, method='tfidf')
        .exclude(similar_to_id__in=seen)
        .values('similar_to_id')
        .annotate(total=Sum('score'))
        .order_by('-total')[:limit]
    )
    ids = [row['similar_to_id'] for row in rows]
    books = Book.objects.prefetch_related('authors').in_bulk(ids)
    return [books[book_id] for book_id in ids if book_id in books]
