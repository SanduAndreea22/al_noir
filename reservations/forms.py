from datetime import date, datetime, timedelta
from decimal import Decimal

from django import forms
from django.db import IntegrityError, transaction
from django.utils import timezone

from menu.models import MenuItem

from .models import Reservation, Table
from operations.models import PromoCode


TIME_CHOICES = [
    ("18:00", "18:00"),
    ("18:30", "18:30"),
    ("19:00", "19:00"),
    ("19:30", "19:30"),
    ("20:00", "20:00"),
    ("20:30", "20:30"),
    ("21:00", "21:00"),
    ("21:30", "21:30"),
    ("22:00", "22:00"),
]


class PricingCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """Adds a machine-readable price to each menu checkbox for the live total."""
    prices = {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option['attrs']['data-price'] = str(self.prices.get(str(value), 0))
        return option


class ReservationForm(forms.ModelForm):

    reservation_time = forms.ChoiceField(
        choices=TIME_CHOICES
    )

    class Meta:

        model = Reservation

        fields = [
            "name",
            "email",
            "phone",
            "reservation_date",
            "reservation_time",
            "guests",
            "selected_items",
            "special_request",
            "promo_code",
        ]

        labels = {
            "special_request": "Special requests",
        }

        widgets = {

            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Full Name"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Email Address"
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number"
            }),

            "reservation_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
                "min": date.today().isoformat()
            }),

            "guests": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "max": 10
            }),

            "selected_items": forms.CheckboxSelectMultiple(),

            "special_request": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Special requests..."
            }),

            "promo_code": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "e.g. WELCOME10"
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["selected_items"].queryset = MenuItem.objects.filter(
            is_available=True
        )
        widget = PricingCheckboxSelectMultiple()
        widget.prices = {str(item.pk): item.price for item in self.fields['selected_items'].queryset}
        self.fields['selected_items'].widget = widget
        self.fields['selected_items'].widget.choices = self.fields['selected_items'].choices

    def clean(self):

        cleaned_data = super().clean()

        reservation_date = cleaned_data.get("reservation_date")
        reservation_time = cleaned_data.get("reservation_time")
        guests = cleaned_data.get("guests")

        if reservation_date is None or reservation_time is None or guests is None:
            return cleaned_data

        if guests < 1:
            raise forms.ValidationError("The number of guests must be at least 1.")

        reservation_time_obj = datetime.strptime(
            reservation_time,
            "%H:%M"
        ).time()

        reservation_datetime = timezone.make_aware(
            datetime.combine(
                reservation_date,
                reservation_time_obj
            )
        )

        if reservation_datetime < timezone.now() + timedelta(hours=2):
            raise forms.ValidationError(
                "Reservations must be made at least 2 hours in advance."
            )

        available_tables = Table.objects.filter(
            status="available",
            capacity__gte=guests
        ).order_by(
            "capacity",
            "number"
        )

        selected_table = None

        for table in available_tables:

            exists = Reservation.objects.filter(
                table=table,
                reservation_date=reservation_date,
                reservation_time=reservation_time_obj,
                status__in=[
                    "pending",
                    "confirmed",
                ]
            ).exists()

            if not exists:
                selected_table = table
                break

        if selected_table is None:
            raise forms.ValidationError(
                "Sorry, the restaurant is fully booked for this time."
            )

        self.selected_table = selected_table

        promo_value = cleaned_data.get('promo_code', '').strip().upper()
        if promo_value:
            try:
                promo = PromoCode.objects.get(code__iexact=promo_value)
                if not promo.is_valid():
                    raise forms.ValidationError('This promo code is no longer valid.')
                cleaned_data['promo_code'] = promo.code
                self.promo = promo
            except PromoCode.DoesNotExist:
                raise forms.ValidationError("This promo code doesn't exist.")

        return cleaned_data

    def save(self, commit=True):

        reservation = super().save(commit=False)

        reservation.table = self.selected_table

        reservation.reservation_time = datetime.strptime(
            self.cleaned_data["reservation_time"],
            "%H:%M"
        ).time()

        promo = getattr(self, 'promo', None)
        selected_items = self.cleaned_data.get('selected_items')
        reservation.advance_amount = sum((item.price for item in selected_items), start=Decimal('0')) * Decimal('0.10')
        if promo:
            reservation.discount_amount = promo.discount_for(reservation.advance_amount)
            reservation.advance_amount = max(0, reservation.advance_amount - reservation.discount_amount)
            if promo.discount_type == PromoCode.FREE_ITEM:
                reservation.promo_free_item = promo.free_item

        if commit:

            try:
                with transaction.atomic():
                    if promo:
                        locked_promo = PromoCode.objects.select_for_update().get(pk=promo.pk)
                        if not locked_promo.is_valid():
                            raise forms.ValidationError('This promo code just expired or reached its usage limit.')
                        locked_promo.register_use()
                    reservation.save()
            except IntegrityError:
                raise forms.ValidationError('Sorry, this table was just booked by someone else. Please try a different time slot.')

            self.save_m2m()

        return reservation
