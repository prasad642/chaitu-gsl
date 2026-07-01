# Incendios Django Backend Guide

## Files created or changed

- `studentapp/models.py`: database tables for all dynamic website content.
- `studentapp/admin.py`: admin panel setup for updating images, posters, text, events, prizes, and messages.
- `studentapp/views.py`: sends database content to each page.
- `studentapp/signals.py`: blocks creating more than one admin account.
- `studentapp/apps.py`: loads the one-admin guard.
- `studentproject/settings.py`: loads the app config.
- `studentapp/migrations/0002_aboutcontent_contactmessage_galleryimage_homefeature_and_more.py`: database migration for the new backend tables.
- `studentapp/templates/students/*.html`: templates now read dynamic data from the database.

## Admin workflow

Open:

```powershell
http://127.0.0.1:8000/admin/
```

Use these admin sections:

- `Home slides`: top homepage carousel posters/images.
- `Home features`: three or more homepage person/cards.
- `Gallery images`: bottom homepage carousel.
- `Council members`: both student council and management council. Choose `Council type`.
- `Events`: cultural, scientific, and sports events with poster, date, time, venue, and text.
- `Info categories`: columns on the information page.
- `Info updates`: notices inside each information category.
- `Prizes`: cultural, sports, and scientific achievements.
- `About content`: editable About page text. Only one About record is allowed.
- `Contact messages`: messages submitted from the Contact page.

## Email setup for OTP

Set these environment variables in `.env` for local development, or in your host dashboard for deployment:

```text
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_TIMEOUT=25
EMAIL_HOST_USER=your-brevo-smtp-login
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
CONTACT_RECEIVER_EMAIL=admin-receiver@gmail.com
```

The app uses Brevo SMTP by default. If email sending fails with `Unauthorized IP address`, open Brevo and authorize the server IP address that is sending mail, or switch these variables to another SMTP provider.

You can also create `studentproject/email_settings.py` for local-only overrides:

```python
EMAIL_HOST_USER = 'your-brevo-smtp-login'
EMAIL_HOST_PASSWORD = 'your-brevo-smtp-key'
CONTACT_RECEIVER_EMAIL = 'admin-receiver@gmail.com'
```

For Gmail, change `EMAIL_HOST` to `smtp.gmail.com`; `EMAIL_HOST_PASSWORD` must be a Gmail app password, not your normal Gmail password.

Test email sending:

```powershell
cd C:\Users\durga\Downloads\chaitu_gsl\studentsproject\studentproject
python manage.py testemail your-email@gmail.com
```

After editing `email_settings.py`, restart `runserver`.

## First setup commands

After fixing/recreating your virtualenv:

```powershell
cd C:\Users\durga\Downloads\chaitu_gsl\studentsproject\studentproject
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Create only one superuser. The project now blocks additional staff/admin users.

`CONTACT_RECEIVER_EMAIL` is the private mailbox that receives Contact Us messages. It is read only on the server and is not shown in the website HTML.

## Image upload notes

Uploaded images go into:

```text
studentproject/media/
```

The project already serves media files during development through `studentproject/urls.py`.
