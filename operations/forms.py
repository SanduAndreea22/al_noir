from datetime import datetime

from django import forms

from reservations.forms import TIME_CHOICES

from .models import Ticket, WaitlistEntry


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('customer_name', 'customer_email', 'quantity')
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError('Please book at least 1 ticket.')
        if quantity > 20:
            raise forms.ValidationError('For 20+ tickets, please contact us directly.')
        return quantity


class WaitlistForm(forms.ModelForm):
    # Same fixed dinner-service slots as ReservationForm, instead of a free-form
    # time picker — the waitlist is for the same service, so the choice of
    # times should match rather than imply anything is available outside them.
    reservation_time = forms.ChoiceField(choices=TIME_CHOICES)

    class Meta:
        model = WaitlistEntry
        fields = ('name', 'email', 'phone', 'reservation_date', 'reservation_time', 'guests', 'notes')
        widgets = {
            'reservation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_reservation_time(self):
        return datetime.strptime(self.cleaned_data['reservation_time'], '%H:%M').time()

    def clean_guests(self):
        guests = self.cleaned_data['guests']
        if guests < 1:
            raise forms.ValidationError('Please add at least 1 guest.')
        if guests > 20:
            raise forms.ValidationError('For groups larger than 20, please contact us directly.')
        return guests
