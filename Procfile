web: python manage.py migrate --noinput && python manage.py ensure_admin && gunicorn studentproject.wsgi:application --bind 0.0.0.0:$PORT
