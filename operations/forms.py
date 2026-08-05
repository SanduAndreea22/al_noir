from django import forms
from .models import Ticket, WaitlistEntry


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('customer_name', 'customer_email', 'quantity')
        widgets = {'customer_name': forms.TextInput(attrs={'class': 'form-control'}), 'customer_email': forms.EmailInput(attrs={'class': 'form-control'}), 'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1})}

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 1:
            raise forms.ValidationError('The number of tickets must be at least 1.')
        return quantity


class WaitlistForm(forms.ModelForm):
    class Meta:
        model = WaitlistEntry
        fields = ('name', 'email', 'phone', 'reservation_date', 'reservation_time', 'guests', 'notes')
        widgets = {
            'reservation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reservation_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_guests(self):
        guests = self.cleaned_data['guests']
        if guests < 1:
            raise forms.ValidationError('The number of guests must be at least 1.')
        return guests
