from django.shortcuts import render

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
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
    entries = (
        request.user.user_books
        .select_related('book')
        .prefetch_related('book__authors')
    )
    shelves = [
        (label, entries.filter(status=value))
        for value, label in UserBook.STATUS_CHOICES
    ]
    return render(request, 'library/my_books.html', {'shelves': shelves})
