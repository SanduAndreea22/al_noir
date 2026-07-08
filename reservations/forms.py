from datetime import date, datetime, timedelta

from django import forms
from django.utils import timezone

from menu.models import MenuItem

from .models import Reservation, Table


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
        ]

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
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["selected_items"].queryset = MenuItem.objects.filter(
            is_available=True
        )

    def clean(self):

        cleaned_data = super().clean()

        reservation_date = cleaned_data.get("reservation_date")
        reservation_time = cleaned_data.get("reservation_time")
        guests = cleaned_data.get("guests")

        if not reservation_date or not reservation_time or not guests:
            return cleaned_data

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

        return cleaned_data

    def save(self, commit=True):

        reservation = super().save(commit=False)

        reservation.table = self.selected_table

        reservation.reservation_time = datetime.strptime(
            self.cleaned_data["reservation_time"],
            "%H:%M"
        ).time()

        if commit:

            reservation.save()

            self.save_m2m()

        return reservation