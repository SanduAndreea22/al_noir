from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem
from .models import Invoice, LoyaltyAccount, Sale, StockItem, StockMovement


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

    def test_staff_can_download_invoice_pdf(self):
        staff = User.objects.create_user('staff', password='test-password', is_staff=True)
        invoice = Invoice.objects.create(number='TEST-001', customer_name='Client Test', description='Servicii', amount=Decimal('100.00'))
        self.client.force_login(staff)
        response = self.client.get(reverse('operations:invoice_pdf', args=[invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_customer_sale_awards_loyalty_points(self):
        customer = User.objects.create_user('client', password='test-password')
        Sale.objects.create(menu_item=self.menu_item, customer=customer, quantity=2, unit_price=Decimal('25.00'))
        self.assertEqual(LoyaltyAccount.objects.get(user=customer).points, 50)
