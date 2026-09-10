from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
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


class CancelReservationTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(number=4, capacity=2)
        self.owner = User.objects.create_user('owner', password='test-password')
        self.other_user = User.objects.create_user('other', password='test-password')
        self.reservation = Reservation.objects.create(
            table=self.table, user=self.owner, name='Owner', email='owner@example.com', phone='0700000004',
            reservation_date=timezone.localdate() + timedelta(days=1), reservation_time='19:00',
            guests=2, status='confirmed',
        )

    def test_owner_can_cancel_their_own_reservation(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('reservations:cancel_reservation', args=[self.reservation.pk]))
        self.assertRedirects(response, reverse('operations:client_dashboard'))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'cancelled')

    def test_another_user_cannot_cancel_someone_elses_reservation(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('reservations:cancel_reservation', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, 404)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'confirmed')

    def test_anonymous_user_is_redirected_to_the_real_login_page(self):
        response = self.client.post(reverse('reservations:cancel_reservation', args=[self.reservation.pk]))
        self.assertEqual(response.status_code, 302)
        expected_next = reverse('reservations:cancel_reservation', args=[self.reservation.pk])
        self.assertEqual(response.url, f"{reverse('login')}?next={expected_next}")
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'confirmed')

    def test_already_cancelled_reservation_stays_cancelled(self):
        self.reservation.status = 'cancelled'
        self.reservation.save(update_fields=['status'])
        self.client.force_login(self.owner)
        self.client.post(reverse('reservations:cancel_reservation', args=[self.reservation.pk]))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'cancelled')


class GroupSizeValidationTests(TestCase):
    def test_group_larger_than_any_table_gets_a_clear_message_not_fully_booked(self):
        Table.objects.create(number=5, capacity=4)
        slot = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=19, minute=0)
        form = ReservationForm(data={
            'name': 'Big Group', 'email': 'group@example.com', 'phone': '0700000005',
            'reservation_date': slot.date(), 'reservation_time': '19:00', 'guests': 12,
        })
        self.assertFalse(form.is_valid())
        errors = list(form.non_field_errors())
        self.assertTrue(any('table large enough' in error for error in errors), errors)
        self.assertFalse(any('fully booked' in error for error in errors), errors)

    def test_group_that_fits_but_all_matching_tables_are_booked_gets_fully_booked_message(self):
        table = Table.objects.create(number=6, capacity=4)
        slot = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
        Reservation.objects.create(
            table=table, name='Existing', email='existing@example.com', phone='0700000006',
            reservation_date=slot.date(), reservation_time=slot.time(), guests=4, status='confirmed',
        )
        form = ReservationForm(data={
            'name': 'New Guest', 'email': 'new@example.com', 'phone': '0700000007',
            'reservation_date': slot.date(), 'reservation_time': '19:00', 'guests': 3,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('fully booked', str(form.errors))

    def test_table_lookup_uses_a_constant_number_of_queries_regardless_of_table_count(self):
        for number in range(7, 17):
            Table.objects.create(number=number, capacity=4)
        slot = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=19, minute=0)
        data = {
            'name': 'Query Count', 'email': 'queries@example.com', 'phone': '0700000008',
            'reservation_date': slot.date(), 'reservation_time': '19:00', 'guests': 2,
        }
        # 1 query to build the menu-item pricing widget (form __init__), plus exactly
        # 2 for table selection (candidate tables, then booked table ids) — fixed
        # regardless of how many tables exist, unlike the old per-table .exists() loop.
        # The remaining 3 are SQLite's application-level validation of the
        # `reservation_guests_gte_1` CheckConstraint (savepoint + check + release);
        # Postgres enforces that constraint natively without extra round-trips.
        with self.assertNumQueries(6):
            form = ReservationForm(data=data)
            self.assertTrue(form.is_valid(), form.errors)


class ReservationConfirmationTests(TestCase):
    def test_confirmation_page_shows_reservation_details(self):
        table = Table.objects.create(number=20, capacity=2)
        reservation = Reservation.objects.create(
            table=table, name='Jane Guest', email='jane@example.com', phone='0700000009',
            reservation_date=timezone.localdate() + timedelta(days=1), reservation_time='19:00',
            guests=2, status='pending',
        )
        response = self.client.get(
            reverse('reservations:confirmation', args=[reservation.pk, reservation.access_token])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Reservation #{reservation.pk}')
        self.assertContains(response, 'Jane Guest')

    def test_confirmation_page_rejects_wrong_token(self):
        table = Table.objects.create(number=21, capacity=2)
        reservation = Reservation.objects.create(
            table=table, name='Jane Guest', email='jane2@example.com', phone='0700000010',
            reservation_date=timezone.localdate() + timedelta(days=1), reservation_time='19:00',
            guests=2, status='pending',
        )
        response = self.client.get(
            reverse('reservations:confirmation', args=[reservation.pk, 'wrong-token'])
        )
        self.assertEqual(response.status_code, 404)

    def test_reservation_without_deposit_redirects_to_confirmation_page(self):
        Table.objects.create(number=22, capacity=4)
        slot = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=19, minute=0)
        response = self.client.post(reverse('reservations:reservations'), data={
            'name': 'No Deposit', 'email': 'nodeposit@example.com', 'phone': '0700000011',
            'reservation_date': slot.date(), 'reservation_time': '19:00', 'guests': 2,
        })
        reservation = Reservation.objects.get(email='nodeposit@example.com')
        self.assertRedirects(
            response,
            reverse('reservations:confirmation', args=[reservation.pk, reservation.access_token])
        )


class GuestsUpperBoundTests(TestCase):
    def test_form_rejects_more_than_10_guests(self):
        Table.objects.create(number=30, capacity=10)
        slot = timezone.localtime(timezone.now() + timedelta(days=1)).replace(hour=19, minute=0)
        form = ReservationForm(data={
            'name': 'Big Party', 'email': 'party@example.com', 'phone': '0700000012',
            'reservation_date': slot.date(), 'reservation_time': '19:00', 'guests': 11,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('table large enough', str(form.errors))

    def test_zero_guests_is_rejected_at_db_level(self):
        table = Table.objects.create(number=31, capacity=4)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Reservation.objects.create(
                    table=table, name='Bad Guest Count', email='bad@example.com', phone='0700000013',
                    reservation_date=timezone.localdate() + timedelta(days=1), reservation_time='19:00',
                    guests=0,
                )
