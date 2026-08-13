from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from menu.models import Category, MenuItem
from .models import Event, Invoice, LoyaltyAccount, Sale, StaffProfile, StockItem, StockMovement, Ticket


class OperationsTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Test')
        self.menu_item = MenuItem.objects.create(category=category, name='Produs test', price=Decimal('25.00'))
        self.stock = StockItem.objects.create(name='Ingredient test', quantity=Decimal('20.00'))

    def test_sale_reduces_stock(self):
        Sale.objects.create(menu_item=self.menu_item, stock_item=self.stock, quantity=2, unit_price=Decimal('25.00'))
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal('18.00'))
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_sale_cannot_reduce_stock_below_zero(self):
        with self.assertRaises(ValueError):
            Sale.objects.create(menu_item=self.menu_item, stock_item=self.stock, quantity=999, unit_price=Decimal('25.00'))
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal('20.00'))
        self.assertEqual(Sale.objects.count(), 0)

    def test_manager_can_download_invoice_pdf(self):
        manager = User.objects.create_user('manager', password='test-password', is_staff=True)
        StaffProfile.objects.create(user=manager, role=StaffProfile.MANAGER)
        invoice = Invoice.objects.create(number='TEST-001', customer_name='Client Test', description='Servicii', amount=Decimal('100.00'))
        self.client.force_login(manager)
        response = self.client.get(reverse('operations:invoice_pdf', args=[invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_non_manager_staff_cannot_download_invoice_pdf(self):
        waiter = User.objects.create_user('waiter', password='test-password', is_staff=True)
        StaffProfile.objects.create(user=waiter, role=StaffProfile.WAITER)
        invoice = Invoice.objects.create(number='TEST-002', customer_name='Client Test', description='Servicii', amount=Decimal('100.00'))
        self.client.force_login(waiter)
        response = self.client.get(reverse('operations:invoice_pdf', args=[invoice.pk]))
        self.assertEqual(response.status_code, 403)

    def test_customer_sale_awards_loyalty_points(self):
        customer = User.objects.create_user('client', password='test-password')
        Sale.objects.create(menu_item=self.menu_item, customer=customer, quantity=2, unit_price=Decimal('25.00'))
        self.assertEqual(LoyaltyAccount.objects.get(user=customer).points, 50)


class EventBookingTests(TestCase):
    def setUp(self):
        self.future_event = Event.objects.create(
            title='Jazz Night', starts_at=timezone.now() + timedelta(days=7),
            capacity=1, ticket_price=Decimal('0'), is_active=True,
        )

    def test_cannot_book_tickets_for_an_event_that_already_happened(self):
        past_event = Event.objects.create(
            title='Old Gala', starts_at=timezone.now() - timedelta(days=1), is_active=True,
        )
        response = self.client.post(reverse('operations:event_booking', args=[past_event.pk]), {
            'customer_name': 'Client Test', 'customer_email': 'client@example.com', 'quantity': 1,
        })
        self.assertRedirects(response, reverse('operations:events'))
        self.assertEqual(Ticket.objects.count(), 0)

    def test_cannot_book_more_tickets_than_remaining_capacity(self):
        Ticket.objects.create(event=self.future_event, customer_name='Existing', customer_email='a@example.com', quantity=1, paid=True)
        response = self.client.post(reverse('operations:event_booking', args=[self.future_event.pk]), {
            'customer_name': 'Client Test', 'customer_email': 'client@example.com', 'quantity': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only 0 spots left')
        self.assertEqual(Ticket.objects.count(), 1)


class ManagerReportAccessTests(TestCase):
    def _staff_user(self, username, role):
        user = User.objects.create_user(username, password='test-password', is_staff=True)
        StaffProfile.objects.create(user=user, role=role)
        return user

    def test_waiter_cannot_view_financial_reports(self):
        self.client.force_login(self._staff_user('waiter', StaffProfile.WAITER))
        response = self.client.get(reverse('operations:staff_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_view_financial_reports(self):
        self.client.force_login(self._staff_user('manager', StaffProfile.MANAGER))
        response = self.client.get(reverse('operations:staff_dashboard'))
        self.assertEqual(response.status_code, 200)
