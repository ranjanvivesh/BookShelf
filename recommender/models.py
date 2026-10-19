from django.db import models
from books.models import Book


class SimilarBook(models.Model):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='similar_from',
    )
    similar_to = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='similar_to_set',
    )
    score = models.FloatField()
    method = models.CharField(max_length=20, default='tfidf')

    class Meta:
        unique_together = ('book', 'similar_to', 'method')
        indexes = [models.Index(fields=['book', 'method', '-score'])]
