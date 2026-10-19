import time

import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from books.models import Author, Book, Genre


BASE = 'https://openlibrary.org'
HEADERS = {'User-Agent': 'BookShelf/0.1 (vivesh61@outlook.com)'}
PAGE = 50


def fetch_description(work_key):
    try:
        response = requests.get(
            f'{BASE}{work_key}.json',
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException:
        return ''

    description = response.json().get('description', '')
    if isinstance(description, dict):
        description = description.get('value', '')
    return description or ''


def fetch_ratings(work_key):
    try:
        response = requests.get(
            f'{BASE}{work_key}/ratings.json',
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None, None

    summary = response.json().get('summary', {})
    return summary.get('average'), summary.get('count')


class Command(BaseCommand):
    help = 'Import books from Open Library by subject, e.g. fantasy science_fiction'

    def add_arguments(self, parser):
        parser.add_argument('subjects', nargs='+')
        parser.add_argument('--limit', type=int, default=100, help='books per subject')
        parser.add_argument('--no-descriptions', action='store_true')

    def handle(self, *args, **options):
        for subject in options['subjects']:
            genre, _ = Genre.objects.get_or_create(
                slug=slugify(subject),
                defaults={'name': subject.replace('_', ' ').title()},
            )
            added = 0

            for offset in range(0, options['limit'], PAGE):
                response = requests.get(
                    f'{BASE}/subjects/{subject}.json',
                    headers=HEADERS,
                    timeout=30,
                    params={'limit': PAGE, 'offset': offset},
                )
                response.raise_for_status()
                works = response.json().get('works', [])
                if not works:
                    break

                for work in works[:options['limit'] - offset]:
                    book, created = Book.objects.get_or_create(
                        ol_key=work['key'],
                        defaults={
                            'title': work['title'][:500],
                            'cover_id': work.get('cover_id'),
                            'published_year': work.get('first_publish_year'),
                        },
                    )
                    if created or book.openlibrary_rating is None:
                        average, count = fetch_ratings(work['key'])
                        if average is not None:
                            book.openlibrary_rating = average
                            book.openlibrary_rating_count = count
                            book.save(update_fields=[
                                'openlibrary_rating',
                                'openlibrary_rating_count',
                            ])
                    if created:
                        added += 1
                        if not options['no_descriptions']:
                            book.description = fetch_description(work['key'])
                            book.save(update_fields=['description'])
                            time.sleep(0.3)
                        for author_data in work.get('authors', []):
                            author, _ = Author.objects.get_or_create(
                                name=author_data['name'][:255]
                            )
                            book.authors.add(author)
                    book.genres.add(genre)

            self.stdout.write(f'{subject}: {added} new books')
