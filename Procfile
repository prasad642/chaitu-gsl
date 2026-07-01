web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn studentproject.wsgi:application --bind 0.0.0.0:$PORT --timeout 60
