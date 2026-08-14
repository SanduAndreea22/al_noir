from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage, Review


class LoginRedirectTests(TestCase):
    def test_login_redirects_to_client_dashboard_not_a_404(self):
        User.objects.create_user('guest', password='test-password')
        response = self.client.post(reverse('login'), {'username': 'guest', 'password': 'test-password'})
        self.assertRedirects(response, reverse('operations:client_dashboard'))


class ContactFormTests(TestCase):
    def _valid_data(self):
        return {
            'name': 'Test Client', 'email': 'client@example.com', 'phone': '0700000000',
            'subject': 'Booking question', 'message': 'Do you have vegan options?',
        }

    def test_valid_submission_creates_message_and_redirects(self):
        response = self.client.post(reverse('contact'), self._valid_data())
        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_invalid_submission_does_not_create_message(self):
        data = self._valid_data()
        data['email'] = 'not-an-email'
        response = self.client.post(reverse('contact'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_ajax_submission_returns_json_success(self):
        response = self.client.post(reverse('contact'), self._valid_data(), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_ajax_submission_with_invalid_data_returns_json_errors(self):
        data = self._valid_data()
        data['email'] = 'not-an-email'
        response = self.client.post(reverse('contact'), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json()['errors'])
        self.assertEqual(ContactMessage.objects.count(), 0)


class ReviewFormTests(TestCase):
    def _valid_data(self):
        return {'name': 'Test Client', 'email': 'client@example.com', 'review_text': 'Great evening!', 'rating': 5}

    def test_new_reviews_are_not_approved_by_default(self):
        self.client.post(reverse('reviews'), self._valid_data())
        review = Review.objects.get()
        self.assertFalse(review.is_approved)

    def test_unapproved_reviews_are_not_listed(self):
        Review.objects.create(name='Hidden', review_text='...', rating=5, is_approved=False)
        response = self.client.get(reverse('reviews'))
        self.assertNotContains(response, 'Hidden')

    def test_approved_reviews_are_listed(self):
        Review.objects.create(name='Visible Guest', review_text='Loved it', rating=5, is_approved=True)
        response = self.client.get(reverse('reviews'))
        self.assertContains(response, 'Visible Guest')

    def test_ajax_submission_returns_json_success(self):
        response = self.client.post(reverse('reviews'), self._valid_data(), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
