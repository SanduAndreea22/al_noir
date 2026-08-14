import logging

from django import forms as django_forms
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from menu.models import Category
from .forms import ReservationForm

logger = logging.getLogger(__name__)


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
        messages.error(request, "Online payment isn't configured yet. Your reservation has been recorded and our team will contact you.")
        return redirect("reservations:reservations")
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            customer_email=reservation.email,
            line_items=[{'price_data': {'currency': 'usd', 'product_data': {'name': f'Al Noir reservation deposit #{reservation.pk}'}, 'unit_amount': int(reservation.advance_amount * 100)}, 'quantity': 1}],
            metadata={'reservation_id': str(reservation.pk)},
            success_url=request.build_absolute_uri(reverse('reservations:payment_success', args=[reservation.pk])) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('reservations:reservations')),
        )
    except ImportError:
        messages.error(request, "The Stripe module is not installed on the server.")
        return redirect("reservations:reservations")
    reservation.stripe_checkout_session_id = session.id
    reservation.save(update_fields=['stripe_checkout_session_id'])
    return redirect(session.url)


def payment_success(request, pk):
    from .models import Reservation
    reservation = get_object_or_404(Reservation, pk=pk)
    session_id = request.GET.get('session_id')
    if settings.STRIPE_SECRET_KEY and session_id and session_id == reservation.stripe_checkout_session_id and not reservation.advance_paid:
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            if stripe.checkout.Session.retrieve(session_id).payment_status == 'paid':
                reservation.advance_paid = True
                reservation.save(update_fields=['advance_paid'])
        except Exception:
            messages.warning(request, 'Your payment is being verified. We will contact you to confirm.')
            return redirect('operations:client_dashboard' if request.user.is_authenticated else 'reservations:reservations')
    if reservation.advance_paid:
        messages.success(request, 'Thank you! Your deposit payment has been confirmed.')
    else:
        messages.warning(request, 'Your payment is being verified. We will contact you to confirm.')
    return redirect('operations:client_dashboard' if request.user.is_authenticated else 'reservations:reservations')


@login_required
@require_POST
def cancel_reservation(request, pk):
    """Lets a logged-in guest cancel their own upcoming reservation from the client dashboard."""
    from .models import Reservation
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    if reservation.status in ('pending', 'confirmed'):
        reservation.status = 'cancelled'
        reservation.save(update_fields=['status'])
        messages.success(request, 'Your reservation has been cancelled.')
    return redirect('operations:client_dashboard')


@csrf_exempt
def stripe_webhook(request):
    """Authoritative Stripe payment confirmation, including cases without a browser redirect."""
    from .models import Reservation
    if request.method != 'POST' or not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest('Webhook unavailable.')
    try:
        import stripe
    except ImportError:
        logger.error('Stripe webhook received but the stripe package is not installed.')
        return HttpResponseBadRequest('Stripe not installed.')
    try:
        event = stripe.Webhook.construct_event(
            request.body, request.META.get('HTTP_STRIPE_SIGNATURE', ''), settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        logger.warning('Stripe webhook rejected: invalid payload or signature.')
        return HttpResponseBadRequest('Invalid signature.')
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        reservation_id = session.get('metadata', {}).get('reservation_id')
        if reservation_id and session.get('payment_status') == 'paid':
            Reservation.objects.filter(pk=reservation_id, stripe_checkout_session_id=session['id']).update(advance_paid=True)
    return HttpResponse(status=200)
