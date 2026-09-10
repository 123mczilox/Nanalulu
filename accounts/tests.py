from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthenticationTestCase(TestCase):
	def test_register_logs_user_in_and_opens_dashboard(self):
		response = self.client.post(
			reverse("register"),
			{
				"username": "new-customer",
				"email": "customer@example.com",
				"password1": "Strong-password-123!",
				"password2": "Strong-password-123!",
			},
		)

		self.assertRedirects(response, reverse("profile"))
		self.assertTrue(response.wsgi_request.user.is_authenticated)
		self.assertContains(self.client.get(reverse("profile")), "Welcome, new-customer")

	def test_profile_requires_login(self):
		response = self.client.get(reverse("profile"))

		self.assertRedirects(
			response,
			f"{reverse('login')}?next={reverse('profile')}",
		)

	def test_logout_clears_session(self):
		User.objects.create_user(username="customer", password="Strong-password-123!")
		self.client.login(username="customer", password="Strong-password-123!")

		response = self.client.post(reverse("logout"))

		self.assertRedirects(response, reverse("home"))
		self.assertFalse(response.wsgi_request.user.is_authenticated)
