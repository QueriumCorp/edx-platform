from __future__ import absolute_import
import os
from os.path import join
from distutils.util import strtobool
from configurations import Configuration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Common(Configuration):
    SECRET_KEY = os.getenv(u'DJANGO_SECRET_KEY')

    # Set DEBUG to False as a default for safety
    # https://docs.djangoproject.com/en/dev/ref/settings/#debug
    DEBUG = strtobool(os.getenv(u'DJANGO_DEBUG', u'no'))

    INSTALLED_APPS = (
    )

    MIDDLEWARE = (
    )

    # Django Rest Framework
    REST_FRAMEWORK = {
        u'DEFAULT_PAGINATION_CLASS': u'rest_framework.pagination.PageNumberPagination',
        u'PAGE_SIZE': int(os.getenv(u'DJANGO_PAGINATION_LIMIT', 10)),
        u'DATETIME_FORMAT': u'%Y-%m-%dT%H:%M:%S%z',
        u'DEFAULT_RENDERER_CLASSES': (
            u'rest_framework.renderers.JSONRenderer',
            u'rest_framework.renderers.BrowsableAPIRenderer',
        ),
        u'DEFAULT_PERMISSION_CLASSES': [
            u'rest_framework.permissions.IsAdminUser',
        ],
        u'DEFAULT_AUTHENTICATION_CLASSES': (
            u'rest_framework.authentication.SessionAuthentication',
            u'rest_framework.authentication.TokenAuthentication',
        )
    }
