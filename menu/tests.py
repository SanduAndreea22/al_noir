from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, MenuItem


class MenuViewTests(TestCase):
    def test_menu_lists_categories_and_available_items(self):
        category = Category.objects.create(name='Starters', order=1)
        MenuItem.objects.create(category=category, name='Bruschetta', price=Decimal('12.00'))
        response = self.client.get(reverse('menu'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Starters')
        self.assertContains(response, 'Bruschetta')

    def test_menu_page_works_with_no_categories(self):
        response = self.client.get(reverse('menu'))
        self.assertEqual(response.status_code, 200)
