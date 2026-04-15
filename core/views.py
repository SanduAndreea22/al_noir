from django.shortcuts import render
from .models import Review


def home(request):
    approved_reviews = Review.objects.filter(is_approved=True)[:3]
    return render(request, 'core/home.html', {
        'approved_reviews': approved_reviews
    })

def about(request):
    return render(request, 'core/about.html')


def reviews(request):
    return render(request, 'core/reviews.html')


def contact(request):
    return render(request, 'core/contact.html')