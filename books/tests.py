from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from library.models import UserBook
from recommender.models import SimilarBook
from recommender.services import recommend_for_user
from .models import Book


class BookShelfTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ann', password='pw12345!')
        self.book = Book.objects.create(
            title='Dune',
            description='desert planet spice',
        )
        self.other = Book.objects.create(
            title='Children of Dune',
            description='desert planet sequel',
        )

    def test_pages_load(self):
        for name in ('home', 'book_list'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        response = self.client.get(reverse('book_detail', args=[self.book.pk]))
        self.assertEqual(response.status_code, 200)

    def test_search_finds_title(self):
        response = self.client.get(reverse('search'), {'q': 'dune'})
        self.assertContains(response, 'Dune')

    def test_save_entry_requires_login(self):
        response = self.client.post(
            reverse('save_entry', args=[self.book.pk]),
            {'rating': '5'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(UserBook.objects.count(), 0)

    def test_save_rating_and_review(self):
        self.client.login(username='ann', password='pw12345!')
        self.client.post(
            reverse('save_entry', args=[self.book.pk]),
            {'status': 'read', 'rating': '5', 'review': 'Great'},
        )
        entry = UserBook.objects.get(user=self.user, book=self.book)
        self.assertEqual(
            (entry.status, entry.rating, entry.review),
            ('read', 5, 'Great'),
        )

    def test_recommendations_skip_seen_books(self):
        UserBook.objects.create(
            user=self.user,
            book=self.book,
            status='read',
            rating=5,
        )
        SimilarBook.objects.create(
            book=self.book,
            similar_to=self.other,
            score=0.8,
        )
        self.assertEqual(recommend_for_user(self.user), [self.other])
