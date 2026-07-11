"""
WSGI config for fir_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fir_project.settings')

django.setup()
try:
    call_command('migrate', '--noinput')
except Exception:
    pass

application = get_wsgi_application()
