from django.urls import path

from . import views


urlpatterns = [
    path('accounts/signup/', views.signup, name='signup'),
    path('my-books/', views.my_books, name='my_books'),
    path('library/save/<int:book_id>/', views.save_entry, name='save_entry'),
]
