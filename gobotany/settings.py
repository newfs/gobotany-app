import urlparse
import os
import sys

try:
    from postgis_paths import GDAL_LIBRARY_PATH, GEOS_LIBRARY_PATH
except ImportError:
    pass

try:
    import debug_toolbar
except:
    DEBUG_TOOLBAR_AVAILABLE = False
else:
    DEBUG_TOOLBAR_AVAILABLE = True

THIS_DIRECTORY = os.path.dirname(__file__)
gettext = lambda s: s

# We define these database specifications as constants, so that we can
# retrieve whichever one we need from our test suites.

REAL_DATABASE = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'gobotany',
    'HOST': '',
    'USER': '',
    'PASSWORD': '',
    }

TEST_DATABASE = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
    'HOST': '',
    'USER': '',
    'PASSWORD': '',
    }

if 'test' in sys.argv:
    DATABASES = {'default': TEST_DATABASE}
else:
    DATABASES = {'default': REAL_DATABASE}

# Are we running in production, where we are free to cache things and in
# general to do things that would annoy a developer making quick changes
# to the application?  We tell by looking for the $PORT environment
# variable, which should always be set on Heroku, and which a developer
# can set locally to test "production" behaviors.  (We do not actually
# do anything with the value, since our Procfile makes it gunicorn's job
# to actually grab the port.)  Note that DEBUG itself can be turned on
# with an explicit environment variable even if we are "in production"
# on Heroku, in case we need Django tracebacks to solve a problem.

IN_PRODUCTION = 'PORT' in os.environ
USE_DEBUG_TOOLBAR = not IN_PRODUCTION and DEBUG_TOOLBAR_AVAILABLE
DEBUG = 'DEBUG' in os.environ or not IN_PRODUCTION

# This setting is for showing features that are still being developed.
# Normally it will be True in local dev environments, and False in
# production. For Heroku dev environments, it can be set to True by
# setting the $DEV_FEATURES environment variable to True, thus allowing
# testing of unreleased things such as the future navigation links.
DEV_FEATURES = not IN_PRODUCTION
if 'DEV_FEATURES' in os.environ:
    DEV_FEATURES = (os.environ['DEV_FEATURES'] == 'True')

#

if 'DATABASE_URL' in os.environ:

    # This code lets script running locally on a developer workstation
    # connect to a Heroku database in the cloud, if its URL provided.
    # This code is adapted from: http://devcenter.heroku.com/articles/django

    url = urlparse.urlparse(os.environ['DATABASE_URL'])

    # Ensure default database exists.
    DATABASES['default'] = DATABASES.get('default', {})

    # Update with environment configuration.
    DATABASES['default'].update({
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
            })

INSTALLED_APPS = [
    'gobotany.api',
    'gobotany.core',
    'gobotany.dkey',
    'gobotany.mapping',
    'gobotany.plantoftheday',
    'gobotany.plantshare',
    'gobotany.search',
    'gobotany.simplekey',
    'gobotany.site',
    'piston',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    ] + (['debug_toolbar'] if USE_DEBUG_TOOLBAR else []) + [

    'haystack',
    'tinymce',
    'facebook_connect',
    'registration',
    'south',
    'captcha',
    ]
MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',

    ) + (('debug_toolbar.middleware.DebugToolbarMiddleware',)
         if USE_DEBUG_TOOLBAR else ()) + (

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'gobotany.middleware.SmartAppendSlashMiddleware',
    'gobotany.middleware.ChromeFrameMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.i18n",
        "django.core.context_processors.request",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "gobotany.core.context_processors.gobotany_specific_context",
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}
APPEND_SLASH = False
SMART_APPEND_SLASH = True
ROOT_URLCONF = 'gobotany.urls'
INTERNAL_IPS = ('127.0.0.1',)
STATIC_URL = '/static/'
STATICFILES_DIRS = [('', os.path.join(THIS_DIRECTORY, 'static'))]
SESSION_COOKIE_AGE = 2 * 24 * 60 * 60  # two days
HAYSTACK_SITECONF = 'gobotany.site.haystack_conf'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8983/solr'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 10
HAYSTACK_SOLR_TIMEOUT = 20  # Longer than default timeout; added for indexing

# For django-facebook-connect
FACEBOOK_LOGIN_REDIRECT = '/ps'     # TODO: /ps/ --> /plantshare/ at release
FACEBOOK_SCOPE = 'email' 
if DEBUG:
# Debug App, on Brandon's account with localhost URL
    FACEBOOK_APP_ID = '190505394309270' 
    FACEBOOK_APP_SECRET = 'eb2dccd2ac2d77dac45a9ee137313d6b' 
else:
# Production App, on NEWFS account with production URL
    FACEBOOK_APP_ID = '174715039247745' 
    FACEBOOK_APP_SECRET = '54f36f2204399f84f127178c8322b5ee' 

# For django-registration
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_URL = '/ps/accounts/login/'   # TODO: /ps/ --> /plantshare/ at release
if DEBUG:
    # To test with this, start a local test email server as follows:
    # python -m smtpd -n -c DebuggingServer localhost:1025
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 1025
else:
    # SendGrid Heroku add-on configuration
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = os.environ['SENDGRID_USERNAME']
    EMAIL_HOST_PASSWORD = os.environ['SENDGRID_PASSWORD']
    USE_TLS = True
    DEFAULT_FROM_EMAIL = 'no-reply@newenglandwild.org'

# For django-recaptcha
if DEBUG:
    # From JR's personal test account, works for domain "localhost"
    RECAPTCHA_PUBLIC_KEY = '6LeJLNYSAAAAADqd4q3EmAEmjcm0fETife_lmHEe'
    RECAPTCHA_PRIVATE_KEY = '6LeJLNYSAAAAADu-quzYmZnGcuBTzq66JMobfQ_Q'
    RECAPTCHA_USE_SSL = True
else:
    # For production use, using domain "newenglandwild.org"
    RECAPTCHA_PUBLIC_KEY = '6LfxLtYSAAAAAOOqRrPQONhKLIOb7sA1jrZHSSz0'
    RECAPTCHA_PRIVATE_KEY = '6LfxLtYSAAAAAP4aYyUyfIsZbEysDxzZmG-DH4J0'
    RECAPTCHA_USE_SSL = True

# For when we are running on Heroku:
if 'WEBSOLR_URL' in os.environ:
    HAYSTACK_SOLR_URL = os.environ['WEBSOLR_URL']

TINYMCE_JS_URL = "tiny_mce/tiny_mce.js"
# With no local static root, what should we do with the following setting?
# TINYMCE_JS_ROOT = os.path.join(STATIC_ROOT, "tiny_mce")

# For partner sites, the request hostname will indicate the site.
MONTSHIRE_HOSTNAME_SUBSTRING = ':8001'  # Just look for a port number for now

# Use memcached for caching if Heroku provides MEMCACHE_SERVERS, or if a
# developer runs us locally with that environment variable set.

if 'MEMCACHE_SERVERS' in os.environ:
    CACHES = {'default': {
        'BACKEND': 'django_pylibmc.memcached.PyLibMCCache'
        }}

# Normally we pull images in read-only mode from our NEWFS S3 bucket.
# Environment variables can be set to provide real AWS keys for writing
# images, or to point the application at an alternative bucket.

if 'test' in sys.argv:
    pass
else:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'readonly')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'readonly')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'newfs')
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_SECURE_URLS = False

# Enable gunicorn sub-command if gunicorn is available.

try:
    import gunicorn
except ImportError:
    pass
else:
    INSTALLED_APPS.append('gunicorn')
