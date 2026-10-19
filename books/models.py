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
    openlibrary_rating = models.FloatField(null=True, blank=True)
    openlibrary_rating_count = models.PositiveIntegerField(null=True, blank=True)
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
