from django.http import JsonResponse
from django.shortcuts import render

from menu.models import Category
from menu.models import MenuItem

from .forms import ReservationForm


def reservations(request):

    categories = Category.objects.prefetch_related(
        'items'
    ).all()

    if request.method == 'POST':

        form = ReservationForm(
            request.POST
        )

        if form.is_valid():

            reservation = form.save()

            selected_items = request.POST.getlist(
                'selected_items'
            )

            items = MenuItem.objects.filter(
                id__in=selected_items
            )

            reservation.selected_items.set(
                items
            )

            return JsonResponse({
                'success': True,
                'message': (
                    'Your reservation has been submitted successfully.'
                )
            })

        return JsonResponse({
            'success': False,
            'errors': form.errors
        })

    form = ReservationForm()

    return render(
        request,
        'reservations/reservations.html',
        {
            'form': form,
            'categories': categories,
        }
    )