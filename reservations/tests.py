from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from menu.models import Category, MenuItem
from .forms import ReservationForm
from .models import Table


class ReservationDepositTests(TestCase):
    def test_selected_menu_items_create_ten_percent_deposit(self):
        category = Category.objects.create(name='Test')
        first = MenuItem.objects.create(category=category, name='Fel principal', price=Decimal('40.00'))
        second = MenuItem.objects.create(category=category, name='Desert', price=Decimal('20.00'))
        Table.objects.create(number=1, capacity=4)
        slot = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=19, minute=0)
        form = ReservationForm(data={
            'name': 'Client Test', 'email': 'client@example.com', 'phone': '0700000000',
            'reservation_date': slot.date(), 'reservation_time': '19:00', 'guests': 2,
            'selected_items': [first.pk, second.pk],
        })
        self.assertTrue(form.is_valid(), form.errors)
        reservation = form.save()
        self.assertEqual(reservation.advance_amount, Decimal('6.00'))

    def test_menu_choices_remain_available_for_the_reservation_form(self):
        category = Category.objects.create(name='Meniu')
        item = MenuItem.objects.create(category=category, name='Paste', price=Decimal('30.00'))
        form = ReservationForm()
        self.assertIn(str(item.pk), str(form['selected_items']))
        self.assertIn('data-price="30.00"', str(form['selected_items']))
