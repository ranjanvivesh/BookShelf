from django.conf import settings
from django.db import models
from books.models import Book


class UserBook(models.Model):
    WANT, READING, READ = 'want', 'reading', 'read'
    STATUS_CHOICES = [
        (WANT, 'Want to read'),
        (READING, 'Currently reading'),
        (READ, 'Read'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_books',
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='user_books',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=WANT)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    review = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
