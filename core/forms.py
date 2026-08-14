from django import forms
from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number (optional)'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your message here...',
                'rows': 6
            }),
        }

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'email', 'review_text', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address (optional)'}),
            'review_text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your experience...', 'rows': 5}),
            'rating': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reversed (5..1), blank choice dropped, so the star-rating CSS
        # sibling-selector trick works: the widget renders radios 5,4,3,2,1 in
        # DOM order, displayed left-to-right via `flex-direction: row-reverse`,
        # so `input:checked ~ label` highlights every star up to and including
        # the checked one. Django auto-adds a blank choice here since the
        # model field has no default; a 6th, valueless "star" would render.
        choices = [choice for choice in self.fields['rating'].choices if choice[0] != '']
        self.fields['rating'].choices = choices[::-1]