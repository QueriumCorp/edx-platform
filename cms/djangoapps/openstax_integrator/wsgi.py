u"""
WSGI config for viral project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/gunicorn/
"""
from __future__ import absolute_import
import os

os.environ.setdefault(u"DJANGO_SETTINGS_MODULE", u"openstax_integrator.config")
os.environ.setdefault(u"DJANGO_CONFIGURATION", u"Local")

from configurations.wsgi import get_wsgi_application  # noqa
application = get_wsgi_application()
