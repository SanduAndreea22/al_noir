from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Favorite, MenuItem, Rating


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


class FavoriteToggleTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Mains')
        self.item = MenuItem.objects.create(category=category, name='Lamb Kabsa', price=Decimal('32.00'))
        self.user = User.objects.create_user('guest', password='test-password')

    def test_anonymous_user_cannot_toggle_favorite(self):
        response = self.client.post(reverse('toggle_favorite', args=[self.item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_logged_in_user_can_favorite_then_unfavorite(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('toggle_favorite', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['favorited'])
        self.assertEqual(Favorite.objects.filter(user=self.user, item=self.item).count(), 1)

        response = self.client.post(reverse('toggle_favorite', args=[self.item.pk]))
        self.assertFalse(response.json()['favorited'])
        self.assertEqual(Favorite.objects.filter(user=self.user, item=self.item).count(), 0)


class RateItemTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Desserts')
        self.item = MenuItem.objects.create(category=category, name='Baklava', price=Decimal('9.00'))
        self.user = User.objects.create_user('guest', password='test-password')

    def test_anonymous_user_cannot_rate(self):
        response = self.client.post(reverse('rate_item', args=[self.item.pk]), {'stars': 5})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Rating.objects.count(), 0)

    def test_rating_is_not_approved_by_default(self):
        self.client.force_login(self.user)
        self.client.post(reverse('rate_item', args=[self.item.pk]), {'stars': 5})
        rating = Rating.objects.get(item=self.item, user=self.user)
        self.assertEqual(rating.stars, 5)
        self.assertFalse(rating.is_approved)

    def test_resubmitting_a_rating_updates_it_instead_of_duplicating(self):
        self.client.force_login(self.user)
        self.client.post(reverse('rate_item', args=[self.item.pk]), {'stars': 3})
        self.client.post(reverse('rate_item', args=[self.item.pk]), {'stars': 5})
        self.assertEqual(Rating.objects.filter(item=self.item, user=self.user).count(), 1)
        self.assertEqual(Rating.objects.get(item=self.item, user=self.user).stars, 5)

    def test_invalid_star_value_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('rate_item', args=[self.item.pk]), {'stars': 9})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Rating.objects.count(), 0)

    def test_only_approved_ratings_count_toward_the_menu_average(self):
        Rating.objects.create(item=self.item, user=self.user, stars=1, is_approved=False)
        response = self.client.get(reverse('menu'))
        self.assertContains(response, 'No ratings yet')

        Rating.objects.filter(item=self.item, user=self.user).update(is_approved=True)
        response = self.client.get(reverse('menu'))
        self.assertNotContains(response, 'No ratings yet')
        self.assertContains(response, '1.0')
