"""
This is the default template for our main set of AWS servers.
"""
# mcdaniel jul-2019: tokenized some of the values in cms.env.json. this converts
#       the values to the actual client code. Example:
#           {CLIENT} = 'dev'
#           {CLIENT}.roverbyopenstax.org becomes: dev.roverbyopenstax.org
def rover_env_token(token, default=None):
    s = str(ENV_TOKENS.get(token, default))
    return s.replace('{CLIENT}', ROVER_CLIENT_CODE)

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

# Pylint gets confused by path.py instances, which report themselves as class
# objects. As a result, pylint applies the wrong regex in validating names,
# and throws spurious errors. Therefore, we disable invalid-name checking.
# pylint: disable=invalid-name

import datetime
import json

from .common import *

from openedx.core.lib.derived import derive_settings
from openedx.core.lib.logsettings import get_logger_config
import os

from path import Path as path
from xmodule.modulestore.modulestore_settings import convert_module_store_setting_if_needed

# SERVICE_VARIANT specifies name of the variant used, which decides what JSON
# configuration files are read during startup.
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

# CONFIG_ROOT specifies the directory where the JSON configuration
# files are expected to be found. If not specified, use the project
# directory.
CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))

# CONFIG_PREFIX specifies the prefix of the JSON configuration files,
# based on the service variant. If no variant is use, don't use a
# prefix.
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""

############### ALWAYS THE SAME ################################

DEBUG = False

EMAIL_BACKEND = 'django_ses.SESBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# IMPORTANT: With this enabled, the server must always be behind a proxy that
# strips the header HTTP_X_FORWARDED_PROTO from client requests. Otherwise,
# a user can fool our server into thinking it was an https connection.
# See
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
# for other warnings.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

###################################### CELERY  ################################

# Don't use a connection pool, since connections are dropped by ELB.
BROKER_POOL_LIMIT = 0
BROKER_CONNECTION_TIMEOUT = 1

# For the Result Store, use the django cache named 'celery'
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'

# When the broker is behind an ELB, use a heartbeat to refresh the
# connection and to detect if it has been dropped.
BROKER_HEARTBEAT = 60.0
BROKER_HEARTBEAT_CHECKRATE = 2

# Each worker should only fetch one message at a time
CELERYD_PREFETCH_MULTIPLIER = 1

# Rename the exchange and queues for each variant

QUEUE_VARIANT = CONFIG_PREFIX.lower()

CELERY_DEFAULT_EXCHANGE = 'edx.{0}core'.format(QUEUE_VARIANT)

HIGH_PRIORITY_QUEUE = 'edx.{0}core.high'.format(QUEUE_VARIANT)
DEFAULT_PRIORITY_QUEUE = 'edx.{0}core.default'.format(QUEUE_VARIANT)
LOW_PRIORITY_QUEUE = 'edx.{0}core.low'.format(QUEUE_VARIANT)

CELERY_DEFAULT_QUEUE = DEFAULT_PRIORITY_QUEUE
CELERY_DEFAULT_ROUTING_KEY = DEFAULT_PRIORITY_QUEUE

CELERY_QUEUES = {
    HIGH_PRIORITY_QUEUE: {},
    LOW_PRIORITY_QUEUE: {},
    DEFAULT_PRIORITY_QUEUE: {}
}

CELERY_ROUTES = "{}celery.Router".format(QUEUE_VARIANT)
CELERYBEAT_SCHEDULE = {}  # For scheduling tasks, entries can be added to this dict

############# NON-SECURE ENV CONFIG ##############################
# Things like server locations, ports, etc.
with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

# McDaniel jul-2019: add a rover-specific client code to be used as a subdomain in some url's
with open("/home/ubuntu/rover/rover.env.json") as rover_env_file:
    ROVER_TOKENS = json.load(rover_env_file)
    ROVER_CLIENT_CODE = ROVER_TOKENS.get('CLIENT_CODE', 'MISSING')


# Do NOT calculate this dynamically at startup with git because it's *slow*.
EDX_PLATFORM_REVISION = rover_env_token('EDX_PLATFORM_REVISION', EDX_PLATFORM_REVISION)

# STATIC_URL_BASE specifies the base url to use for static files
STATIC_URL_BASE = rover_env_token('STATIC_URL_BASE', None)
if STATIC_URL_BASE:
    # collectstatic will fail if STATIC_URL is a unicode string
    STATIC_URL = STATIC_URL_BASE.encode('ascii')
    if not STATIC_URL.endswith("/"):
        STATIC_URL += "/"
    STATIC_URL += 'studio/'


# DEFAULT_COURSE_ABOUT_IMAGE_URL specifies the default image to show for courses that don't provide one
DEFAULT_COURSE_ABOUT_IMAGE_URL = rover_env_token('DEFAULT_COURSE_ABOUT_IMAGE_URL', DEFAULT_COURSE_ABOUT_IMAGE_URL)

DEFAULT_COURSE_VISIBILITY_IN_CATALOG = rover_env_token(
    'DEFAULT_COURSE_VISIBILITY_IN_CATALOG',
    DEFAULT_COURSE_VISIBILITY_IN_CATALOG
)

# DEFAULT_MOBILE_AVAILABLE specifies if the course is available for mobile by default
DEFAULT_MOBILE_AVAILABLE = rover_env_token(
    'DEFAULT_MOBILE_AVAILABLE',
    DEFAULT_MOBILE_AVAILABLE
)

# MEDIA_ROOT specifies the directory where user-uploaded files are stored.
MEDIA_ROOT = rover_env_token('MEDIA_ROOT', MEDIA_ROOT)
MEDIA_URL = rover_env_token('MEDIA_URL', MEDIA_URL)

# GITHUB_REPO_ROOT is the base directory
# for course data
GITHUB_REPO_ROOT = rover_env_token('GITHUB_REPO_ROOT', GITHUB_REPO_ROOT)

# STATIC_ROOT specifies the directory where static files are
# collected

STATIC_ROOT_BASE = rover_env_token('STATIC_ROOT_BASE', None)
if STATIC_ROOT_BASE:
    STATIC_ROOT = path(STATIC_ROOT_BASE) / 'studio'
    WEBPACK_LOADER['DEFAULT']['STATS_FILE'] = STATIC_ROOT / "webpack-stats.json"

EMAIL_BACKEND = rover_env_token('EMAIL_BACKEND', EMAIL_BACKEND)
EMAIL_FILE_PATH = rover_env_token('EMAIL_FILE_PATH', None)

EMAIL_HOST = rover_env_token('EMAIL_HOST', EMAIL_HOST)
EMAIL_PORT = rover_env_token('EMAIL_PORT', EMAIL_PORT)
EMAIL_USE_TLS = rover_env_token('EMAIL_USE_TLS', EMAIL_USE_TLS)

LMS_BASE = rover_env_token('LMS_BASE')
LMS_ROOT_URL = rover_env_token('LMS_ROOT_URL')
LMS_INTERNAL_ROOT_URL = rover_env_token('LMS_INTERNAL_ROOT_URL', LMS_ROOT_URL)
ENTERPRISE_API_URL = rover_env_token('ENTERPRISE_API_URL', LMS_INTERNAL_ROOT_URL + '/enterprise/api/v1/')
ENTERPRISE_CONSENT_API_URL = rover_env_token('ENTERPRISE_CONSENT_API_URL', LMS_INTERNAL_ROOT_URL + '/consent/api/v1/')
# Note that FEATURES['PREVIEW_LMS_BASE'] gets read in from the environment file.

SITE_NAME = ENV_TOKENS['SITE_NAME']

ALLOWED_HOSTS = [
    # TODO: bbeggs remove this before prod, temp fix to get load testing running
    "*",
    rover_env_token('CMS_BASE')
]

LOG_DIR = ENV_TOKENS['LOG_DIR']
DATA_DIR = path(rover_env_token('DATA_DIR', DATA_DIR))

CACHES = ENV_TOKENS['CACHES']
# Cache used for location mapping -- called many times with the same key/value
# in a given request.
if 'loc_cache' not in CACHES:
    CACHES['loc_cache'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    }

SESSION_COOKIE_DOMAIN = rover_env_token('SESSION_COOKIE_DOMAIN')
SESSION_COOKIE_HTTPONLY = rover_env_token('SESSION_COOKIE_HTTPONLY', True)
SESSION_ENGINE = rover_env_token('SESSION_ENGINE', SESSION_ENGINE)
SESSION_COOKIE_SECURE = rover_env_token('SESSION_COOKIE_SECURE', SESSION_COOKIE_SECURE)
SESSION_SAVE_EVERY_REQUEST = rover_env_token('SESSION_SAVE_EVERY_REQUEST', SESSION_SAVE_EVERY_REQUEST)

# social sharing settings
SOCIAL_SHARING_SETTINGS = rover_env_token('SOCIAL_SHARING_SETTINGS', SOCIAL_SHARING_SETTINGS)

REGISTRATION_EMAIL_PATTERNS_ALLOWED = rover_env_token('REGISTRATION_EMAIL_PATTERNS_ALLOWED')

# allow for environments to specify what cookie name our login subsystem should use
# this is to fix a bug regarding simultaneous logins between edx.org and edge.edx.org which can
# happen with some browsers (e.g. Firefox)
if rover_env_token('SESSION_COOKIE_NAME', None):
    # NOTE, there's a bug in Django (http://bugs.python.org/issue18012) which necessitates this being a str()
    SESSION_COOKIE_NAME = str(rover_env_token('SESSION_COOKIE_NAME'))

# Set the names of cookies shared with the marketing site
# These have the same cookie domain as the session, which in production
# usually includes subdomains.
EDXMKTG_LOGGED_IN_COOKIE_NAME = rover_env_token('EDXMKTG_LOGGED_IN_COOKIE_NAME', EDXMKTG_LOGGED_IN_COOKIE_NAME)
EDXMKTG_USER_INFO_COOKIE_NAME = rover_env_token('EDXMKTG_USER_INFO_COOKIE_NAME', EDXMKTG_USER_INFO_COOKIE_NAME)

# Determines whether the CSRF token can be transported on
# unencrypted channels. It is set to False here for backward compatibility,
# but it is highly recommended that this is True for environments accessed
# by end users.
CSRF_COOKIE_SECURE = rover_env_token('CSRF_COOKIE_SECURE', False)

#Email overrides
DEFAULT_FROM_EMAIL = rover_env_token('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
DEFAULT_FEEDBACK_EMAIL = rover_env_token('DEFAULT_FEEDBACK_EMAIL', DEFAULT_FEEDBACK_EMAIL)
ADMINS = rover_env_token('ADMINS', ADMINS)
SERVER_EMAIL = rover_env_token('SERVER_EMAIL', SERVER_EMAIL)
MKTG_URLS = rover_env_token('MKTG_URLS', MKTG_URLS)
MKTG_URL_LINK_MAP.update(rover_env_token('MKTG_URL_LINK_MAP', {}))
TECH_SUPPORT_EMAIL = rover_env_token('TECH_SUPPORT_EMAIL', TECH_SUPPORT_EMAIL)

for name, value in rover_env_token("CODE_JAIL", {}).items():
    oldvalue = CODE_JAIL.get(name)
    if isinstance(oldvalue, dict):
        for subname, subvalue in value.items():
            oldvalue[subname] = subvalue
    else:
        CODE_JAIL[name] = value

COURSES_WITH_UNSAFE_CODE = rover_env_token("COURSES_WITH_UNSAFE_CODE", [])

ASSET_IGNORE_REGEX = rover_env_token('ASSET_IGNORE_REGEX', ASSET_IGNORE_REGEX)

# McDaniel jul-2019: hard-coding this to simplify edxapp json config file.
#COMPREHENSIVE_THEME_DIRS = rover_env_token('COMPREHENSIVE_THEME_DIRS', COMPREHENSIVE_THEME_DIRS) or []
COMPREHENSIVE_THEME_DIRS = ['/edx/app/edxapp/edx-platform/themes']

# COMPREHENSIVE_THEME_LOCALE_PATHS contain the paths to themes locale directories e.g.
# "COMPREHENSIVE_THEME_LOCALE_PATHS" : [
#        "/edx/src/edx-themes/conf/locale"
#    ],
COMPREHENSIVE_THEME_LOCALE_PATHS = rover_env_token('COMPREHENSIVE_THEME_LOCALE_PATHS', [])

DEFAULT_SITE_THEME = rover_env_token('DEFAULT_SITE_THEME', DEFAULT_SITE_THEME)
ENABLE_COMPREHENSIVE_THEMING = rover_env_token('ENABLE_COMPREHENSIVE_THEMING', ENABLE_COMPREHENSIVE_THEMING)

#Timezone overrides
TIME_ZONE = rover_env_token('TIME_ZONE', TIME_ZONE)

# Push to LMS overrides
GIT_REPO_EXPORT_DIR = rover_env_token('GIT_REPO_EXPORT_DIR', '/edx/var/edxapp/export_course_repos')

# Translation overrides
LANGUAGES = rover_env_token('LANGUAGES', LANGUAGES)
LANGUAGE_CODE = rover_env_token('LANGUAGE_CODE', LANGUAGE_CODE)
LANGUAGE_COOKIE = rover_env_token('LANGUAGE_COOKIE', LANGUAGE_COOKIE)

USE_I18N = rover_env_token('USE_I18N', USE_I18N)
ALL_LANGUAGES = rover_env_token('ALL_LANGUAGES', ALL_LANGUAGES)

ENV_FEATURES = rover_env_token('FEATURES', {})
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

# Additional installed apps
for app in rover_env_token('ADDL_INSTALLED_APPS', []):
    INSTALLED_APPS.append(app)

WIKI_ENABLED = rover_env_token('WIKI_ENABLED', WIKI_ENABLED)

LOGGING = get_logger_config(LOG_DIR,
                            logging_env=ENV_TOKENS['LOGGING_ENV'],
                            service_variant=SERVICE_VARIANT)

#theming start:
PLATFORM_NAME = rover_env_token('PLATFORM_NAME', PLATFORM_NAME)
PLATFORM_DESCRIPTION = rover_env_token('PLATFORM_DESCRIPTION', PLATFORM_DESCRIPTION)
STUDIO_NAME = rover_env_token('STUDIO_NAME', STUDIO_NAME)
STUDIO_SHORT_NAME = rover_env_token('STUDIO_SHORT_NAME', STUDIO_SHORT_NAME)

# Event Tracking
if "TRACKING_IGNORE_URL_PATTERNS" in ENV_TOKENS:
    TRACKING_IGNORE_URL_PATTERNS = rover_env_token("TRACKING_IGNORE_URL_PATTERNS")

# Heartbeat
HEARTBEAT_CHECKS = rover_env_token('HEARTBEAT_CHECKS', HEARTBEAT_CHECKS)
HEARTBEAT_EXTENDED_CHECKS = rover_env_token('HEARTBEAT_EXTENDED_CHECKS', HEARTBEAT_EXTENDED_CHECKS)
HEARTBEAT_CELERY_TIMEOUT = rover_env_token('HEARTBEAT_CELERY_TIMEOUT', HEARTBEAT_CELERY_TIMEOUT)

# Django CAS external authentication settings
CAS_EXTRA_LOGIN_PARAMS = rover_env_token("CAS_EXTRA_LOGIN_PARAMS", None)
if FEATURES.get('AUTH_USE_CAS'):
    CAS_SERVER_URL = rover_env_token("CAS_SERVER_URL", None)
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'django_cas.backends.CASBackend',
    ]

    INSTALLED_APPS.append('django_cas')

    MIDDLEWARE_CLASSES.append('django_cas.middleware.CASMiddleware')
    CAS_ATTRIBUTE_CALLBACK = rover_env_token('CAS_ATTRIBUTE_CALLBACK', None)
    if CAS_ATTRIBUTE_CALLBACK:
        import importlib
        CAS_USER_DETAILS_RESOLVER = getattr(
            importlib.import_module(CAS_ATTRIBUTE_CALLBACK['module']),
            CAS_ATTRIBUTE_CALLBACK['function']
        )

# Specific setting for the File Upload Service to store media in a bucket.
FILE_UPLOAD_STORAGE_BUCKET_NAME = rover_env_token('FILE_UPLOAD_STORAGE_BUCKET_NAME', FILE_UPLOAD_STORAGE_BUCKET_NAME)
FILE_UPLOAD_STORAGE_PREFIX = rover_env_token('FILE_UPLOAD_STORAGE_PREFIX', FILE_UPLOAD_STORAGE_PREFIX)

# Zendesk
ZENDESK_URL = rover_env_token('ZENDESK_URL', ZENDESK_URL)
ZENDESK_CUSTOM_FIELDS = rover_env_token('ZENDESK_CUSTOM_FIELDS', ZENDESK_CUSTOM_FIELDS)

################ SECURE AUTH ITEMS ###############################
# Secret things: passwords, access keys, etc.
with open(CONFIG_ROOT / CONFIG_PREFIX + "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

############### XBlock filesystem field config ##########
if 'DJFS' in AUTH_TOKENS and AUTH_TOKENS['DJFS'] is not None:
    DJFS = AUTH_TOKENS['DJFS']
    if 'url_root' in DJFS:
        DJFS['url_root'] = DJFS['url_root'].format(platform_revision=EDX_PLATFORM_REVISION)

EMAIL_HOST_USER = AUTH_TOKENS.get('EMAIL_HOST_USER', EMAIL_HOST_USER)
EMAIL_HOST_PASSWORD = AUTH_TOKENS.get('EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD)

AWS_SES_REGION_NAME = rover_env_token('AWS_SES_REGION_NAME', 'us-east-1')
AWS_SES_REGION_ENDPOINT = rover_env_token('AWS_SES_REGION_ENDPOINT', 'email.us-east-1.amazonaws.com')

# Note that this is the Studio key for Segment. There is a separate key for the LMS.
CMS_SEGMENT_KEY = AUTH_TOKENS.get('SEGMENT_KEY')

SECRET_KEY = AUTH_TOKENS['SECRET_KEY']

AWS_ACCESS_KEY_ID = AUTH_TOKENS["AWS_ACCESS_KEY_ID"]
if AWS_ACCESS_KEY_ID == "":
    AWS_ACCESS_KEY_ID = None

AWS_SECRET_ACCESS_KEY = AUTH_TOKENS["AWS_SECRET_ACCESS_KEY"]
if AWS_SECRET_ACCESS_KEY == "":
    AWS_SECRET_ACCESS_KEY = None

AWS_STORAGE_BUCKET_NAME = AUTH_TOKENS.get('AWS_STORAGE_BUCKET_NAME', 'edxuploads')

# Disabling querystring auth instructs Boto to exclude the querystring parameters (e.g. signature, access key) it
# normally appends to every returned URL.
AWS_QUERYSTRING_AUTH = AUTH_TOKENS.get('AWS_QUERYSTRING_AUTH', True)

AWS_DEFAULT_ACL = 'private'
AWS_BUCKET_ACL = AWS_DEFAULT_ACL
AWS_QUERYSTRING_EXPIRE = 7 * 24 * 60 * 60  # 7 days
AWS_S3_CUSTOM_DOMAIN = AUTH_TOKENS.get('AWS_S3_CUSTOM_DOMAIN', 'edxuploads.s3.amazonaws.com')

if AUTH_TOKENS.get('DEFAULT_FILE_STORAGE'):
    DEFAULT_FILE_STORAGE = AUTH_TOKENS.get('DEFAULT_FILE_STORAGE')
elif AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

COURSE_IMPORT_EXPORT_BUCKET = rover_env_token('COURSE_IMPORT_EXPORT_BUCKET', '')

if COURSE_IMPORT_EXPORT_BUCKET:
    COURSE_IMPORT_EXPORT_STORAGE = 'contentstore.storage.ImportExportS3Storage'
else:
    COURSE_IMPORT_EXPORT_STORAGE = DEFAULT_FILE_STORAGE

USER_TASKS_ARTIFACT_STORAGE = COURSE_IMPORT_EXPORT_STORAGE

DATABASES = AUTH_TOKENS['DATABASES']

# The normal database user does not have enough permissions to run migrations.
# Migrations are run with separate credentials, given as DB_MIGRATION_*
# environment variables
for name, database in DATABASES.items():
    if name != 'read_replica':
        database.update({
            'ENGINE': os.environ.get('DB_MIGRATION_ENGINE', database['ENGINE']),
            'USER': os.environ.get('DB_MIGRATION_USER', database['USER']),
            'PASSWORD': os.environ.get('DB_MIGRATION_PASS', database['PASSWORD']),
            'NAME': os.environ.get('DB_MIGRATION_NAME', database['NAME']),
            'HOST': os.environ.get('DB_MIGRATION_HOST', database['HOST']),
            'PORT': os.environ.get('DB_MIGRATION_PORT', database['PORT']),
        })

MODULESTORE = convert_module_store_setting_if_needed(AUTH_TOKENS.get('MODULESTORE', MODULESTORE))

MODULESTORE_FIELD_OVERRIDE_PROVIDERS = rover_env_token(
    'MODULESTORE_FIELD_OVERRIDE_PROVIDERS',
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS
)

XBLOCK_FIELD_DATA_WRAPPERS = rover_env_token(
    'XBLOCK_FIELD_DATA_WRAPPERS',
    XBLOCK_FIELD_DATA_WRAPPERS
)

CONTENTSTORE = AUTH_TOKENS['CONTENTSTORE']
DOC_STORE_CONFIG = AUTH_TOKENS['DOC_STORE_CONFIG']
# Datadog for events!
DATADOG = AUTH_TOKENS.get("DATADOG", {})
DATADOG.update(rover_env_token("DATADOG", {}))

# TODO: deprecated (compatibility with previous settings)
if 'DATADOG_API' in AUTH_TOKENS:
    DATADOG['api_key'] = AUTH_TOKENS['DATADOG_API']

# Celery Broker
CELERY_ALWAYS_EAGER = rover_env_token("CELERY_ALWAYS_EAGER", False)
CELERY_BROKER_TRANSPORT = rover_env_token("CELERY_BROKER_TRANSPORT", "")
CELERY_BROKER_HOSTNAME = rover_env_token("CELERY_BROKER_HOSTNAME", "")
CELERY_BROKER_VHOST = rover_env_token("CELERY_BROKER_VHOST", "")
CELERY_BROKER_USER = AUTH_TOKENS.get("CELERY_BROKER_USER", "")
CELERY_BROKER_PASSWORD = AUTH_TOKENS.get("CELERY_BROKER_PASSWORD", "")

BROKER_URL = "{0}://{1}:{2}@{3}/{4}".format(CELERY_BROKER_TRANSPORT,
                                            CELERY_BROKER_USER,
                                            CELERY_BROKER_PASSWORD,
                                            CELERY_BROKER_HOSTNAME,
                                            CELERY_BROKER_VHOST)
BROKER_USE_SSL = rover_env_token('CELERY_BROKER_USE_SSL', False)

# Message expiry time in seconds
CELERY_EVENT_QUEUE_TTL = rover_env_token('CELERY_EVENT_QUEUE_TTL', None)

# Allow CELERY_QUEUES to be overwritten by ENV_TOKENS,
ENV_CELERY_QUEUES = rover_env_token('CELERY_QUEUES', None)
if ENV_CELERY_QUEUES:
    CELERY_QUEUES = {queue: {} for queue in ENV_CELERY_QUEUES}

# Then add alternate environment queues
ALTERNATE_QUEUE_ENVS = rover_env_token('ALTERNATE_WORKER_QUEUES', '').split()
ALTERNATE_QUEUES = [
    DEFAULT_PRIORITY_QUEUE.replace(QUEUE_VARIANT, alternate + '.')
    for alternate in ALTERNATE_QUEUE_ENVS
]

CELERY_QUEUES.update(
    {
        alternate: {}
        for alternate in ALTERNATE_QUEUES
        if alternate not in CELERY_QUEUES.keys()
    }
)

# Queue to use for updating grades due to grading policy change
POLICY_CHANGE_GRADES_ROUTING_KEY = rover_env_token('POLICY_CHANGE_GRADES_ROUTING_KEY', LOW_PRIORITY_QUEUE)

# Rate limit for regrading tasks that a grading policy change can kick off
POLICY_CHANGE_TASK_RATE_LIMIT = rover_env_token('POLICY_CHANGE_TASK_RATE_LIMIT', POLICY_CHANGE_TASK_RATE_LIMIT)

# Event tracking
TRACKING_BACKENDS.update(AUTH_TOKENS.get("TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['tracking_logs']['OPTIONS']['backends'].update(AUTH_TOKENS.get("EVENT_TRACKING_BACKENDS", {}))
EVENT_TRACKING_BACKENDS['segmentio']['OPTIONS']['processors'][0]['OPTIONS']['whitelist'].extend(
    AUTH_TOKENS.get("EVENT_TRACKING_SEGMENTIO_EMIT_WHITELIST", []))

##### ACCOUNT LOCKOUT DEFAULT PARAMETERS #####
MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED = rover_env_token("MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED", 5)
MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS = rover_env_token("MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS", 15 * 60)

#### PASSWORD POLICY SETTINGS #####
PASSWORD_MIN_LENGTH = rover_env_token("PASSWORD_MIN_LENGTH")
PASSWORD_MAX_LENGTH = rover_env_token("PASSWORD_MAX_LENGTH")
PASSWORD_COMPLEXITY = rover_env_token("PASSWORD_COMPLEXITY", {})
PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD = rover_env_token("PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD")
PASSWORD_DICTIONARY = rover_env_token("PASSWORD_DICTIONARY", [])

### INACTIVITY SETTINGS ####
SESSION_INACTIVITY_TIMEOUT_IN_SECONDS = AUTH_TOKENS.get("SESSION_INACTIVITY_TIMEOUT_IN_SECONDS")

##### X-Frame-Options response header settings #####
X_FRAME_OPTIONS = rover_env_token('X_FRAME_OPTIONS', X_FRAME_OPTIONS)

##### Third-party auth options ################################################
##
## added by mcdaniel Feb-2019. copied from lms aws.py
if FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    tmp_backends = rover_env_token('THIRD_PARTY_AUTH_BACKENDS', [
        'social_core.backends.google.GoogleOAuth2',
        'social_core.backends.linkedin.LinkedinOAuth2',
        'social_core.backends.facebook.FacebookOAuth2',
        'social_core.backends.azuread.AzureADOAuth2',
        'third_party_auth.saml.SAMLAuthBackend',
        'third_party_auth.lti.LTIAuthBackend',
        'openstax_oauth_backend.openstax.OpenStaxOAuth2',
    ])

    AUTHENTICATION_BACKENDS = list(tmp_backends) + list(AUTHENTICATION_BACKENDS)
    del tmp_backends

    # The reduced session expiry time during the third party login pipeline. (Value in seconds)
    SOCIAL_AUTH_PIPELINE_TIMEOUT = rover_env_token('SOCIAL_AUTH_PIPELINE_TIMEOUT', 600)

    # Most provider configuration is done via ConfigurationModels but for a few sensitive values
    # we allow configuration via AUTH_TOKENS instead (optionally).
    # The SAML private/public key values do not need the delimiter lines (such as
    # "-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----" etc.) but they may be included
    # if you want (though it's easier to format the key values as JSON without the delimiters).
    SOCIAL_AUTH_SAML_SP_PRIVATE_KEY = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY', '')
    SOCIAL_AUTH_SAML_SP_PUBLIC_CERT = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PUBLIC_CERT', '')
    SOCIAL_AUTH_SAML_SP_PRIVATE_KEY_DICT = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PRIVATE_KEY_DICT', {})
    SOCIAL_AUTH_SAML_SP_PUBLIC_CERT_DICT = AUTH_TOKENS.get('SOCIAL_AUTH_SAML_SP_PUBLIC_CERT_DICT', {})
    SOCIAL_AUTH_OAUTH_SECRETS = AUTH_TOKENS.get('SOCIAL_AUTH_OAUTH_SECRETS', {})
    SOCIAL_AUTH_LTI_CONSUMER_SECRETS = AUTH_TOKENS.get('SOCIAL_AUTH_LTI_CONSUMER_SECRETS', {})

    # third_party_auth config moved to ConfigurationModels. This is for data migration only:
    THIRD_PARTY_AUTH_OLD_CONFIG = AUTH_TOKENS.get('THIRD_PARTY_AUTH', None)

    if rover_env_token('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24) is not None:
        CELERYBEAT_SCHEDULE['refresh-saml-metadata'] = {
            'task': 'third_party_auth.fetch_saml_metadata',
            'schedule': datetime.timedelta(hours=rover_env_token('THIRD_PARTY_AUTH_SAML_FETCH_PERIOD_HOURS', 24)),
        }

    # The following can be used to integrate a custom login form with third_party_auth.
    # It should be a dict where the key is a word passed via ?auth_entry=, and the value is a
    # dict with an arbitrary 'secret_key' and a 'url'.
    THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS = AUTH_TOKENS.get('THIRD_PARTY_AUTH_CUSTOM_AUTH_FORMS', {})


##### ADVANCED_SECURITY_CONFIG #####
ADVANCED_SECURITY_CONFIG = rover_env_token('ADVANCED_SECURITY_CONFIG', {})

################ ADVANCED COMPONENT/PROBLEM TYPES ###############

ADVANCED_PROBLEM_TYPES = rover_env_token('ADVANCED_PROBLEM_TYPES', ADVANCED_PROBLEM_TYPES)

################ VIDEO UPLOAD PIPELINE ###############

VIDEO_UPLOAD_PIPELINE = rover_env_token('VIDEO_UPLOAD_PIPELINE', VIDEO_UPLOAD_PIPELINE)

################ VIDEO IMAGE STORAGE ###############

VIDEO_IMAGE_SETTINGS = rover_env_token('VIDEO_IMAGE_SETTINGS', VIDEO_IMAGE_SETTINGS)

################ VIDEO TRANSCRIPTS STORAGE ###############

VIDEO_TRANSCRIPTS_SETTINGS = rover_env_token('VIDEO_TRANSCRIPTS_SETTINGS', VIDEO_TRANSCRIPTS_SETTINGS)

################ PUSH NOTIFICATIONS ###############

PARSE_KEYS = AUTH_TOKENS.get("PARSE_KEYS", {})


# Video Caching. Pairing country codes with CDN URLs.
# Example: {'CN': 'http://api.xuetangx.com/edx/video?s3_url='}
VIDEO_CDN_URL = rover_env_token('VIDEO_CDN_URL', {})

if FEATURES['ENABLE_COURSEWARE_INDEX'] or FEATURES['ENABLE_LIBRARY_INDEX']:
    # Use ElasticSearch for the search engine
    SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

ELASTIC_SEARCH_CONFIG = rover_env_token('ELASTIC_SEARCH_CONFIG', [{}])

XBLOCK_SETTINGS = rover_env_token('XBLOCK_SETTINGS', {})
XBLOCK_SETTINGS.setdefault("VideoDescriptor", {})["licensing_enabled"] = FEATURES.get("LICENSING", False)
XBLOCK_SETTINGS.setdefault("VideoModule", {})['YOUTUBE_API_KEY'] = AUTH_TOKENS.get('YOUTUBE_API_KEY', YOUTUBE_API_KEY)

################# PROCTORING CONFIGURATION ##################

PROCTORING_BACKEND_PROVIDER = AUTH_TOKENS.get("PROCTORING_BACKEND_PROVIDER", PROCTORING_BACKEND_PROVIDER)
PROCTORING_SETTINGS = rover_env_token("PROCTORING_SETTINGS", PROCTORING_SETTINGS)

################# MICROSITE ####################
# microsite specific configurations.
MICROSITE_CONFIGURATION = rover_env_token('MICROSITE_CONFIGURATION', {})
MICROSITE_ROOT_DIR = path(rover_env_token('MICROSITE_ROOT_DIR', ''))
# this setting specify which backend to be used when pulling microsite specific configuration
MICROSITE_BACKEND = rover_env_token("MICROSITE_BACKEND", MICROSITE_BACKEND)
# this setting specify which backend to be used when loading microsite specific templates
MICROSITE_TEMPLATE_BACKEND = rover_env_token("MICROSITE_TEMPLATE_BACKEND", MICROSITE_TEMPLATE_BACKEND)
# TTL for microsite database template cache
MICROSITE_DATABASE_TEMPLATE_CACHE_TTL = rover_env_token(
    "MICROSITE_DATABASE_TEMPLATE_CACHE_TTL", MICROSITE_DATABASE_TEMPLATE_CACHE_TTL
)

############################ OAUTH2 Provider ###################################
if FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    OAUTH_OIDC_ISSUER = ENV_TOKENS['OAUTH_OIDC_ISSUER']
    OAUTH_ENFORCE_SECURE = rover_env_token('OAUTH_ENFORCE_SECURE', True)
    OAUTH_ENFORCE_CLIENT_SECURE = rover_env_token('OAUTH_ENFORCE_CLIENT_SECURE', True)
    # Defaults for the following are defined in lms.envs.common
    OAUTH_EXPIRE_DELTA = datetime.timedelta(
        days=rover_env_token('OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS', OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS)
    )
    OAUTH_EXPIRE_DELTA_PUBLIC = datetime.timedelta(
        days=rover_env_token('OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS', OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS)
    )
    OAUTH_ID_TOKEN_EXPIRATION = rover_env_token('OAUTH_ID_TOKEN_EXPIRATION', OAUTH_ID_TOKEN_EXPIRATION)
    OAUTH_DELETE_EXPIRED = rover_env_token('OAUTH_DELETE_EXPIRED', OAUTH_DELETE_EXPIRED)


#### JWT configuration ####
JWT_AUTH.update(rover_env_token('JWT_AUTH', {}))

######################## CUSTOM COURSES for EDX CONNECTOR ######################
if FEATURES.get('CUSTOM_COURSES_EDX'):
    INSTALLED_APPS.append('openedx.core.djangoapps.ccxcon.apps.CCXConnectorConfig')

# Partner support link for CMS footer
PARTNER_SUPPORT_EMAIL = rover_env_token('PARTNER_SUPPORT_EMAIL', PARTNER_SUPPORT_EMAIL)

# Affiliate cookie tracking
AFFILIATE_COOKIE_NAME = rover_env_token('AFFILIATE_COOKIE_NAME', AFFILIATE_COOKIE_NAME)

############## Settings for Studio Context Sensitive Help ##############

HELP_TOKENS_BOOKS = rover_env_token('HELP_TOKENS_BOOKS', HELP_TOKENS_BOOKS)

############## Settings for CourseGraph ############################
COURSEGRAPH_JOB_QUEUE = rover_env_token('COURSEGRAPH_JOB_QUEUE', LOW_PRIORITY_QUEUE)

########################## Parental controls config  #######################

# The age at which a learner no longer requires parental consent, or None
# if parental consent is never required.
PARENTAL_CONSENT_AGE_LIMIT = rover_env_token(
    'PARENTAL_CONSENT_AGE_LIMIT',
    PARENTAL_CONSENT_AGE_LIMIT
)

########################## Extra middleware classes  #######################

# Allow extra middleware classes to be added to the app through configuration.
MIDDLEWARE_CLASSES.extend(rover_env_token('EXTRA_MIDDLEWARE_CLASSES', []))

########################## Settings for Completion API #####################

# Once a user has watched this percentage of a video, mark it as complete:
# (0.0 = 0%, 1.0 = 100%)
COMPLETION_VIDEO_COMPLETE_PERCENTAGE = rover_env_token(
    'COMPLETION_VIDEO_COMPLETE_PERCENTAGE',
    COMPLETION_VIDEO_COMPLETE_PERCENTAGE,
)

####################### Enterprise Settings ######################
# A shared secret to be used for encrypting passwords passed from the enterprise api
# to the enteprise reporting script.
ENTERPRISE_REPORTING_SECRET = AUTH_TOKENS.get(
    'ENTERPRISE_REPORTING_SECRET',
    ENTERPRISE_REPORTING_SECRET
)

############### Settings for Retirement #####################
RETIRED_USERNAME_PREFIX = rover_env_token('RETIRED_USERNAME_PREFIX', RETIRED_USERNAME_PREFIX)
RETIRED_EMAIL_PREFIX = rover_env_token('RETIRED_EMAIL_PREFIX', RETIRED_EMAIL_PREFIX)
RETIRED_EMAIL_DOMAIN = rover_env_token('RETIRED_EMAIL_DOMAIN', RETIRED_EMAIL_DOMAIN)
RETIREMENT_SERVICE_WORKER_USERNAME = rover_env_token(
    'RETIREMENT_SERVICE_WORKER_USERNAME',
    RETIREMENT_SERVICE_WORKER_USERNAME
)
RETIREMENT_STATES = rover_env_token('RETIREMENT_STATES', RETIREMENT_STATES)

####################### Plugin Settings ##########################

from openedx.core.djangoapps.plugins import plugin_settings, constants as plugin_constants
plugin_settings.add_plugins(__name__, plugin_constants.ProjectType.CMS, plugin_constants.SettingsType.AWS)

########################## Derive Any Derived Settings  #######################

derive_settings(__name__)

# McDaniel jul-2019: add querium apps
INSTALLED_APPS.append('openstax_integrator.salesforce')

# mcdaniel mar-2019: Openstax Backend parameters
OPENSTAX_BACKEND_CLIENT_ID = 'd9c46de5a97776843189e8e2f77b96ae51333a814b1f91afcbae481d9ee734be'
OPENSTAX_BACKEND_CLIENT_SECRET = 'b615e6ea4a66743f2d2bbc9d1561b59efc87c5f378a4d2203d5ca2365e1b593a'
OPENSTAX_BACKEND_AUTHORIZATION_URL = 'https://accounts.openstax.org/oauth/authorize'
OPENSTAX_BACKEND_ACCESS_TOKEN_URL = 'https://accounts.openstax.org/oauth/token'
OPENSTAX_BACKEND_USER_QUERY = 'https://accounts.openstax.org/api/user?'
OPENSTAX_BACKEND_USERS_QUERY = 'https://accounts.openstax.org/api/users?'

# mcdaniel feb-2019 - add REDIRECT_AM_REGISTRATION
REDIRECT_AM_REGISTRATION = rover_env_token('REDIRECT_AM_REGISTRATION', '')
