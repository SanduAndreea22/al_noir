# Development notes

Technical reference for working on this codebase. See [README.md](README.md) for a plain-language overview of the project.

## Tech stack

- **Backend:** Django 5.2
- **Database:** PostgreSQL (Neon) in production, SQLite for local dev
- **Payments:** Stripe Checkout + webhooks
- **Media storage:** Cloudinary
- **Static files:** WhiteNoise
- **Hosting:** Render (gunicorn, auto-deploy on push to `main`)
- **PDF generation:** for reservation invoices

## Architecture

The project is split into four Django apps by domain:

| App | Responsibility |
|---|---|
| `core` | Site settings, contact messages, reviews |
| `menu` | Menu categories and items |
| `reservations` | Tables, reservations, Stripe checkout/webhook |
| `operations` | Everything staff-facing: stock, sales, expenses, events, tickets, invoices, loyalty, promo codes, staff shifts, waitlist |

## Deployment notes

- **Zero hardcoded secrets** — `SECRET_KEY`, database URL, Stripe keys, and Cloudinary credentials are all environment variables; the app refuses to start in production without a real `SECRET_KEY`.
- **No shell access on Render's free tier**, so there's no way to run `createsuperuser` interactively — solved with an idempotent `ensure_superuser` management command that runs on every deploy from `DJANGO_SUPERUSER_*` env vars.
- **`STORAGES` vs `STATICFILES_STORAGE`** — Django 4.2+'s new `STORAGES` setting and `django-cloudinary-storage` (which only reads the legacy `STATICFILES_STORAGE`) had to be configured in parallel, plus `--upload-unhashed-files` on `collectstatic`, or static assets silently failed to deploy.
- **`SECURE_PROXY_SSL_HEADER` + `CSRF_TRUSTED_ORIGINS`** configured for Render's reverse proxy so CSRF checks and `request.is_secure()` behave correctly behind it.
- `render.yaml` documents the intended Blueprint config, but the actual service was created manually through the Render dashboard (Blueprint deploys required a card on file at the time) — so the dashboard, not that file, is the live source of truth. Update both together if the setup changes.

## Running locally

```bash
git clone https://github.com/SanduAndreea22/al_noir.git
cd al_noir
python -m venv venv
venv\Scripts\activate        # or: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # fill in your own values
python manage.py migrate
python manage.py runserver
```

Required environment variables are listed in `.env.example`. At minimum, local development needs `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=True`; Stripe and Cloudinary keys are only needed to exercise those specific features.

## Audit history

This project went through three audit-and-remediation passes before being considered production-ready: security/data-integrity, then design/UX/copy, then a full reservation-flow redesign. Every fix was verified locally (`manage.py check`, `manage.py test`, and manual functional testing) before being committed — see commit history for the full list. A plain-language summary of the real bugs found and fixed is in the [README](README.md#built-to-hold-up-under-real-use).
