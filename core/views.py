from .forms import ContactMessageForm
from django.shortcuts import redirect, render
from .models import Review
from .forms import ReviewForm
from .utils import form_json_response, is_ajax
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm


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
        if is_ajax(request):
            return form_json_response(form, 'Your message has been sent successfully.')
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully.')
            return redirect('contact')
    else:
        form = ContactMessageForm()

    return render(request, 'core/contact.html', {
        'form': form
    })

def reviews(request):
    reviews_list = Review.objects.filter(is_approved=True).order_by('-created_at')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if is_ajax(request):
            return form_json_response(form, 'Thank you! Your review will be visible after approval.')
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you! Your review will be visible after approval.')
            return redirect('reviews')
    else:
        form = ReviewForm()

    return render(request, 'core/reviews.html', {
        'reviews': reviews_list,
        'form': form
    })


def privacy(request):
    return render(request, 'core/privacy.html')

def terms(request):
    return render(request, 'core/terms.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('operations:client_dashboard')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your account has been created.')
        return redirect('operations:client_dashboard')
    return render(request, 'registration/register.html', {'form': form})
