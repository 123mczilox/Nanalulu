# Liquor Store A

## Local development

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:

   ```bash
   python -m venv env
   source env/bin/activate
   ```

   On Windows PowerShell, activate it with `env\Scripts\Activate.ps1`.
3. Install the project dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```
4. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

   Replace `DJANGO_SECRET_KEY` in `.env` with a generated value, for example:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

   Keep `.env` private; it is excluded from version control.
5. Create the local SQLite database and start the server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

   Open <http://127.0.0.1:8000/>. Create an admin account with
   `python manage.py createsuperuser` if needed.

The site displays an 18+ confirmation popup and remembers confirmation in the
current browser. This is a client-side age gate, not identity or legal-age
verification.

The contact form sends messages to `CONTACT_EMAIL_TO` (defaults to the
placeholder `contact@example.com`). Replace this with the business's real
contact address before launch. During development, Django writes submitted messages to
the runserver terminal. To send real email, configure the SMTP values in
`.env` and set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`.
For production, use your mail provider's SMTP credentials and configure
`DEFAULT_FROM_EMAIL` to an address allowed by that provider.

M-Pesa credentials are not required to run the site. To test payments, set the
M-Pesa values in `.env` and use a public HTTPS callback URL; a local callback
address cannot receive Safaricom requests.
