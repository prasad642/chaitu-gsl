# Deployment Guide

Use this inner project folder as the deploy root:

```text
D:\GSL\chaitu_gsl\chaitu_gsl\studentsproject\studentproject
```

Do not upload `env/`, `build/`, `dist/`, `__pycache__/`, `db.sqlite3`, or `studentproject/email_settings.py`.

## Required environment variables

```text
DEBUG=False
SECRET_KEY=<generate-a-long-random-secret>
ALLOWED_HOSTS=web-production-6b6b2.up.railway.app
CSRF_TRUSTED_ORIGINS=https://web-production-6b6b2.up.railway.app
EMAIL_HOST_USER=<gmail-sender-address>
EMAIL_HOST_PASSWORD=<gmail-app-password>
CONTACT_RECEIVER_EMAIL=<admin-receiver-address>
```

For MySQL, add these variables:

```text
DB_ENGINE=mysql
MYSQL_DATABASE=<database-name>
MYSQL_USER=<database-user>
MYSQL_PASSWORD=<database-password>
MYSQL_HOST=<database-host>
MYSQL_PORT=3306
```

Optional HTTPS settings:

```text
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

Only enable the HSTS subdomain/preload settings after confirming all subdomains use HTTPS.

## Build command

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

## Start command

```bash
gunicorn studentproject.wsgi:application --bind 0.0.0.0:$PORT
```

The `Procfile` already contains this start command for platforms that detect it automatically.

## Important storage note

This project currently uses SQLite and local uploaded media. On hosts with temporary filesystems, uploaded images and the SQLite database can disappear after redeploy/restart unless you configure persistent storage. For a college/admin site, use a host with persistent disk support, a VPS, PythonAnywhere, or move the database/media to managed services before relying on it in production.
