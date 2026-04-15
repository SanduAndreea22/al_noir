from django.urls import path
from .views import home, about, reviews, contact

urlpatterns = [
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('reviews/', reviews, name='reviews'),
    path('contact/', contact, name='contact'),
]