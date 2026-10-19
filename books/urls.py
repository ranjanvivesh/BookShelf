from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('search/', views.search, name='search'),
    path('books/import-open-library/', views.import_open_library, name='import_open_library'),
]
