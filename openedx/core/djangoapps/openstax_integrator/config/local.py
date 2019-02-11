from __future__ import absolute_import
import os
from os.path import join
from distutils.util import strtobool
from .common import Common
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Local(Common):
    DEBUG = True

    # Custom user app for development
    AUTH_USER_MODEL = u'users.User'


    ALLOWED_HOSTS = [u"*"]
    ROOT_URLCONF = u'openstax_integrator.urls'
    WSGI_APPLICATION = u'openstax_integrator.wsgi.application'

    # Email
    EMAIL_BACKEND = u'django.core.mail.backends.smtp.EmailBackend'

    ADMINS = (
        (u'Author', u'lpm0073@gmail.com'),
    )

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/
    STATIC_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), u'static'))
    STATICFILES_DIRS = []
    STATIC_URL = u'/static/'
    STATICFILES_FINDERS = (
        u'django.contrib.staticfiles.finders.FileSystemFinder',
        u'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )

    # Media files
    MEDIA_ROOT = join(os.path.dirname(BASE_DIR), u'media')
    MEDIA_URL = u'/media/'

    TEMPLATES = [
        {
            u'BACKEND': u'django.template.backends.django.DjangoTemplates',
            u'DIRS': STATICFILES_DIRS,
            u'APP_DIRS': True,
            u'OPTIONS': {
                u'context_processors': [
                    u'django.template.context_processors.debug',
                    u'django.template.context_processors.request',
                    u'django.contrib.auth.context_processors.auth',
                    u'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    # sqlite3
    DATABASES = {
        u'default': {
            u'ENGINE': u'django.db.backends.sqlite3',
            u'NAME': os.path.join(BASE_DIR, u'db.sqlite3'),
        }
    }

    # General
    APPEND_SLASH = False
    TIME_ZONE = u'UTC'
    LANGUAGE_CODE = u'en-us'
    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = False
    USE_L10N = True
    USE_TZ = True
    LOGIN_REDIRECT_URL = u'/'

    # https://docs.djangoproject.com/en/2.0/topics/http/middleware/
    MIDDLEWARE = Common.MIDDLEWARE
    MIDDLEWARE += (
        u'django.middleware.security.SecurityMiddleware',
        u'django.contrib.sessions.middleware.SessionMiddleware',
        u'django.middleware.common.CommonMiddleware',
        u'django.middleware.csrf.CsrfViewMiddleware',
        u'django.contrib.auth.middleware.AuthenticationMiddleware',
        u'django.contrib.messages.middleware.MessageMiddleware',
        u'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )

    # Testing
    INSTALLED_APPS = Common.INSTALLED_APPS

    INSTALLED_APPS += (
        u'django.contrib.admin',
        u'django.contrib.auth',
        u'django.contrib.contenttypes',
        u'django.contrib.sessions',
        u'django.contrib.messages',
        u'django.contrib.staticfiles',


        # Third party apps
        u'rest_framework',            # utilities for rest apis
        u'rest_framework.authtoken',  # token authentication
        u'django_filters',            # for filtering rest endpoints
        u'rest_framework_swagger',

        # Your apps
        u'openstax_integrator.users',
        u'openstax_integrator.salesforce',
        u'openstax_integrator.course_creators',

    )


    NOSE_ARGS = [
        BASE_DIR,
        u'-s',
        u'--nologcapture',
        u'--with-coverage',
        u'--with-progressive',
        u'--cover-package=openstax-integrator'
    ]

    # Mail
    EMAIL_HOST = u'localhost'
    EMAIL_PORT = 1025
    EMAIL_BACKEND = u'django.core.mail.backends.console.EmailBackend'

    # Password Validation
    # https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#module-django.contrib.auth.password_validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            u'NAME': u'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            u'NAME': u'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            u'NAME': u'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            u'NAME': u'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    # Logging
    LOGGING = {
        u'version': 1,
        u'disable_existing_loggers': False,
        u'formatters': {
            u'django.server': {
                u'()': u'django.utils.log.ServerFormatter',
                u'format': u'[%(server_time)s] %(message)s',
            },
            u'verbose': {
                u'format': u'%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
            u'simple': {
                u'format': u'%(levelname)s %(message)s'
            },
        },
        u'filters': {
            u'require_debug_true': {
                u'()': u'django.utils.log.RequireDebugTrue',
            },
        },
        u'handlers': {
            u'django.server': {
                u'level': u'INFO',
                u'class': u'logging.StreamHandler',
                u'formatter': u'django.server',
            },
            u'console': {
                u'level': u'DEBUG',
                u'class': u'logging.StreamHandler',
                u'formatter': u'simple'
            },
            u'mail_admins': {
                u'level': u'ERROR',
                u'class': u'django.utils.log.AdminEmailHandler'
            }
        },
        u'loggers': {
            u'django': {
                u'handlers': [u'console'],
                u'propagate': True,
            },
            u'django.server': {
                u'handlers': [u'django.server'],
                u'level': u'INFO',
                u'propagate': False,
            },
            u'django.request': {
                u'handlers': [u'mail_admins', u'console'],
                u'level': u'ERROR',
                u'propagate': False,
            },
            u'django.db.backends': {
                u'handlers': [u'console'],
                u'level': u'INFO'
            },
        }
    }
