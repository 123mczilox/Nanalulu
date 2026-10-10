from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings


class AgeVerificationTestCase(TestCase):
    def test_site_pages_include_blocking_age_verification(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="age-verification"')
        self.assertContains(response, 'aria-modal="true"')
        self.assertContains(response, "I am 18 or older")
        self.assertContains(response, "I am under 18")


class ContactPageTestCase(TestCase):
    def test_contact_page_renders(self):
        response = self.client.get("/contact/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact Liquor Store A")
        self.assertContains(response, "contact@example.com")
        self.assertContains(response, "Send us a message")

    @override_settings(CONTACT_EMAIL_TO="shop@example.com")
    def test_valid_contact_form_emails_message_and_redirects(self):
        response = self.client.post(
            "/contact/",
            {
                "name": "Test Customer",
                "email": "customer@example.com",
                "subject": "Delivery question",
                "message": "When will my order arrive?",
            },
            follow=True,
        )

        self.assertRedirects(
            response,
            "/contact/",
            status_code=302,
            target_status_code=200,
        )
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ["shop@example.com"])
        self.assertEqual(sent_email.reply_to, ["customer@example.com"])
        self.assertIn("[Liquor Store A Contact] Delivery question", sent_email.subject)
        self.assertIn("When will my order arrive?", sent_email.body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
    )
    def test_console_backend_explains_message_is_not_emailed(self):
        with patch("core.views.EmailMessage.send", return_value=1):
            response = self.client.post(
                "/contact/",
                {
                    "name": "Test Customer",
                    "email": "customer@example.com",
                    "subject": "Delivery question",
                    "message": "When will my order arrive?",
                },
                follow=True,
            )

        self.assertContains(response, "written to the development server console")

    def test_invalid_contact_form_does_not_send_email(self):
        response = self.client.post(
            "/contact/",
            {
                "name": "Test Customer",
                "email": "not-an-email",
                "subject": "Delivery question",
                "message": "When will my order arrive?",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address.")
        self.assertEqual(len(mail.outbox), 0)

    def test_email_backend_failure_is_reported(self):
        with patch(
            "core.views.EmailMessage.send",
            side_effect=OSError("SMTP unavailable"),
        ):
            response = self.client.post(
                "/contact/",
                {
                    "name": "Test Customer",
                    "email": "customer@example.com",
                    "subject": "Delivery question",
                    "message": "When will my order arrive?",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                "We couldn't send your message right now." in str(message)
                for message in response.context["messages"]
            )
        )
