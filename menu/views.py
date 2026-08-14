from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import Category, Favorite, MenuItem, Rating


@ensure_csrf_cookie
def menu(request):
    items = MenuItem.objects.annotate(
        avg_rating=Avg('ratings__stars', filter=Q(ratings__is_approved=True)),
        rating_count=Count('ratings', filter=Q(ratings__is_approved=True)),
    )
    categories = Category.objects.prefetch_related(Prefetch('items', queryset=items)).all()

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list('item_id', flat=True))

    return render(request, 'menu/menu.html', {
        'categories': categories,
        'favorite_ids': favorite_ids,
    })


@login_required
@require_POST
def toggle_favorite(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    favorite = Favorite.objects.filter(user=request.user, item=item).first()
    if favorite:
        favorite.delete()
        favorited = False
    else:
        Favorite.objects.create(user=request.user, item=item)
        favorited = True
    return JsonResponse({'favorited': favorited})


@login_required
@require_POST
def rate_item(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    try:
        stars = int(request.POST.get('stars', 0))
    except (TypeError, ValueError):
        stars = 0
    if not 1 <= stars <= 5:
        return JsonResponse({'error': 'Invalid rating.'}, status=400)
    Rating.objects.update_or_create(item=item, user=request.user, defaults={'stars': stars, 'is_approved': False})
    return JsonResponse({'success': True, 'message': 'Thanks! Your rating will be visible after approval.'})
