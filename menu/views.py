from django.shortcuts import render
from .models import Category

def menu(request):
    categories = Category.objects.prefetch_related('items').all()

    return render(request, 'menu/menu.html', {
        'categories': categories
    })