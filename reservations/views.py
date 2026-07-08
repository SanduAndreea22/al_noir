from django.contrib import messages
from django.shortcuts import redirect, render

from menu.models import Category
from .forms import ReservationForm


def reservations(request):

    categories = Category.objects.prefetch_related(
        "items"
    ).all()

    if request.method == "POST":

        form = ReservationForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your reservation has been sent successfully! We will confirm it shortly."
            )

            return redirect("reservations:reservations")

    else:

        form = ReservationForm()

    context = {
        "form": form,
        "categories": categories,
    }

    return render(
        request,
        "reservations/reservations.html",
        context,
    )