from .forms import ContactMessageForm
from django.shortcuts import render
from django.http import JsonResponse
from .models import Review
from .forms import ReviewForm


def home(request):
    approved_reviews = Review.objects.filter(is_approved=True)[:3]
    return render(request, 'core/home.html', {
        'approved_reviews': approved_reviews
    })

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Your message has been sent successfully.'
            })
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)

    form = ContactMessageForm()
    return render(request, 'core/contact.html', {
        'form': form
    })

def reviews(request):
    reviews_list = Review.objects.filter(is_approved=True).order_by('-created_at')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Thank you! Your review will be visible after approval.'
            })
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)

    form = ReviewForm()

    return render(request, 'core/reviews.html', {
        'reviews': reviews_list,
        'form': form
    })