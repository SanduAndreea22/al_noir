from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from menu.models import Category, MenuItem


class HomeMenuPreviewTests(TestCase):
    def test_home_lists_available_dishes_only_and_caps_items(self):
        starters = Category.objects.create(name='Starters', order=1)
        for i in range(4):
            MenuItem.objects.create(category=starters, name=f'Dish {i}', price=Decimal('7.00'))
        MenuItem.objects.create(category=starters, name='Hidden dish', price=Decimal('9.00'), is_available=False)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        preview = response.context['menu_preview']
        self.assertEqual(len(preview), 1)
        category, items = preview[0]
        self.assertEqual(category.name, 'Starters')
        self.assertEqual(len(items), 3)
        self.assertNotContains(response, 'Hidden dish')

    def test_home_without_menu_renders_without_teaser(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['menu_preview'], [])
        self.assertNotContains(response, 'A taste of the evening')

    def test_empty_categories_are_skipped(self):
        Category.objects.create(name='Empty', order=1)
        full = Category.objects.create(name='Mains', order=2)
        MenuItem.objects.create(category=full, name='Kabsa', price=Decimal('22.00'))
        preview = self.client.get(reverse('home')).context['menu_preview']
        self.assertEqual([c.name for c, _ in preview], ['Mains'])
