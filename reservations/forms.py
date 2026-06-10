from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from .models import Reservation


class ReservationForm(forms.ModelForm):

    class Meta:
        model = Reservation

        fields = [
            'name',
            'email',
            'phone',
            'reservation_date',
            'reservation_time',
            'guests',
            'special_request',
        ]

    def clean(self):

        cleaned_data = super().clean()

        reservation_date = cleaned_data.get(
            'reservation_date'
        )

        reservation_time = cleaned_data.get(
            'reservation_time'
        )

        if reservation_date and reservation_time:

            reservation_datetime = datetime.combine(
                reservation_date,
                reservation_time
            )

            reservation_datetime = timezone.make_aware(
                reservation_datetime
            )

            minimum_time = (
                timezone.now()
                + timedelta(hours=2)
            )

            if reservation_datetime < minimum_time:

                raise forms.ValidationError(
                    "Reservations must be made at least 2 hours in advance."
                )

        return cleaned_data