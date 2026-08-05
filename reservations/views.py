from django import forms as django_forms
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from menu.models import Category
from .forms import ReservationForm


def reservations(request):

    categories = Category.objects.prefetch_related(
        "items"
    ).all()

    if request.method == "POST":

        form = ReservationForm(request.POST)

        if form.is_valid():

            try:
                reservation = form.save()
            except django_forms.ValidationError as exc:
                form.add_error(None, exc)
            else:
                if request.user.is_authenticated:
                    reservation.user = request.user
                    reservation.save(update_fields=['user'])

                if reservation.advance_amount > 0:
                    return redirect("reservations:checkout", pk=reservation.pk, token=reservation.access_token)

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


def checkout(request, pk, token):
    """Create a Stripe Checkout session for a reservation advance."""
    from .models import Reservation
    reservation = get_object_or_404(Reservation, pk=pk, access_token=token)
    if reservation.advance_paid or reservation.advance_amount <= 0:
        return redirect("reservations:reservations")
    if not settings.STRIPE_SECRET_KEY:
        messages.error(request, "Plata online nu este configurată încă. Rezervarea a fost înregistrată, iar echipa noastră te va contacta.")
        return redirect("reservations:reservations")
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            customer_email=reservation.email,
            line_items=[{'price_data': {'currency': 'ron', 'product_data': {'name': f'Avans rezervare Al Noir #{reservation.pk}'}, 'unit_amount': int(reservation.advance_amount * 100)}, 'quantity': 1}],
            metadata={'reservation_id': str(reservation.pk)},
            success_url=request.build_absolute_uri(reverse('reservations:payment_success', args=[reservation.pk])) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('reservations:reservations')),
        )
    except ImportError:
        messages.error(request, "Modulul Stripe nu este instalat pe server.")
        return redirect("reservations:reservations")
    reservation.stripe_checkout_session_id = session.id
    reservation.save(update_fields=['stripe_checkout_session_id'])
    return redirect(session.url)


def payment_success(request, pk):
    from .models import Reservation
    reservation = get_object_or_404(Reservation, pk=pk)
    session_id = request.GET.get('session_id')
    if settings.STRIPE_SECRET_KEY and session_id and session_id == reservation.stripe_checkout_session_id:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            if stripe.checkout.Session.retrieve(session_id).payment_status == 'paid':
                reservation.advance_paid = True
                reservation.save(update_fields=['advance_paid'])
        except Exception:
            messages.warning(request, 'Plata este în verificare. Te vom contacta pentru confirmare.')
            return redirect('operations:client_dashboard' if request.user.is_authenticated else 'reservations:reservations')
    messages.success(request, 'Mulțumim! Plata avansului a fost confirmată.')
    return redirect('operations:client_dashboard' if request.user.is_authenticated else 'reservations:reservations')


@csrf_exempt
def stripe_webhook(request):
    """Authoritative Stripe payment confirmation, including cases without a browser redirect."""
    from .models import Reservation
    if request.method != 'POST' or not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest('Webhook indisponibil.')
    try:
        import stripe
        event = stripe.Webhook.construct_event(
            request.body, request.META.get('HTTP_STRIPE_SIGNATURE', ''), settings.STRIPE_WEBHOOK_SECRET
        )
    except (ImportError, ValueError, Exception):
        return HttpResponseBadRequest('Semnătură invalidă.')
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        reservation_id = session.get('metadata', {}).get('reservation_id')
        if reservation_id and session.get('payment_status') == 'paid':
            Reservation.objects.filter(pk=reservation_id, stripe_checkout_session_id=session['id']).update(advance_paid=True)
    return HttpResponse(status=200)
