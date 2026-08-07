from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from menu.models import Category, MenuItem
from .forms import ReservationForm
from .models import Reservation, Table


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


class DoubleBookingTests(TestCase):
    def test_same_table_slot_cannot_be_booked_twice_at_db_level(self):
        table = Table.objects.create(number=2, capacity=4)
        slot = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0)
        Reservation.objects.create(
            table=table, name='First', email='first@example.com', phone='0700000001',
            reservation_date=slot.date(), reservation_time=slot.time(), guests=2, status='pending',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservation.objects.create(
                    table=table, name='Second', email='second@example.com', phone='0700000002',
                    reservation_date=slot.date(), reservation_time=slot.time(), guests=2, status='confirmed',
                )


class CheckoutAccessTests(TestCase):
    def test_checkout_rejects_wrong_access_token(self):
        table = Table.objects.create(number=3, capacity=2)
        reservation = Reservation.objects.create(
            table=table, name='Client', email='client@example.com', phone='0700000003',
            reservation_date=timezone.localdate() + timedelta(days=1), reservation_time='19:00',
            guests=2, advance_amount=Decimal('10.00'),
        )
        response = self.client.get(reverse('reservations:checkout', args=[reservation.pk, 'wrong-token']))
        self.assertEqual(response.status_code, 404)
