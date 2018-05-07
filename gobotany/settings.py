import urlparse
import os
import sys

try:
    import debug_toolbar
except:
    DEBUG_TOOLBAR_AVAILABLE = False
else:
    DEBUG_TOOLBAR_AVAILABLE = True

THIS_DIRECTORY = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(THIS_DIRECTORY)
gettext = lambda s: s

# Django Secret Key (required in Django >= 1.5)
SECRET_KEY = os.environ.get('GOBOTANY_DJANGO_SECRET_KEY', '')

# New in Django 1.5: allowed hosts required for production-like deployments
ALLOWED_HOSTS = ['.newenglandwild.org', # any subdomain of newenglandwild.org
    'gobotany-dev.herokuapp.com',
    'gobotany-staging.herokuapp.com',
    'gobotany-prod.herokuapp.com',
    'localhost',
    '127.0.0.1',
    '0.0.0.0'
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_ROOT, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'gobotany.core.context_processors.gobotany_specific_context',
            ],
            'debug': False,
        },
    },
]

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

USE_DEBUG_TOOLBAR = False
# Django Debug Toolbar is turned off by default. Uncomment the
# following line to turn it on.
#USE_DEBUG_TOOLBAR = not IN_PRODUCTION and DEBUG_TOOLBAR_AVAILABLE

DEBUG_TOOLBAR_PATCH_SETTINGS = False

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'haystack_panel.panel.HaystackDebugPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

DEBUG = (('DEBUG' in os.environ and os.environ['DEBUG'] == 'True')
    or not IN_PRODUCTION)

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
    'gobotany.editor',
    'gobotany.mapping',
    'gobotany.plantoftheday',
    'gobotany.plantpreview',
    'gobotany.plantshare',
    'gobotany.search',
    'gobotany.simplekey',
    'gobotany.site',
    'gobotany.taxa',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    ] + (['debug_toolbar'] if USE_DEBUG_TOOLBAR else []) + [

    'haystack',
    'haystack_panel',
    'imagekit',
    'tinymce',
    'registration',
    #'emailconfirmation', # Temporarily uncomment to create this app's
                          # tables using syncdb. This will also allow
                          # the app's tables to be visible in the Admin.
                          # Otherwise, keep this app commented out in
                          # order to avoid a NoMigrations error when
                          # applying South migrations.
                          # Update: also keep commented out for the Django 1.7
                          # upgrade when running: dev/django makemigrations
    'captcha',
    ]
MIDDLEWARE_CLASSES = (
    ) + (('sslify.middleware.SSLifyMiddleware',)
         if IN_PRODUCTION else ()) + (

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.gzip.GZipMiddleware',

    ) + (('debug_toolbar.middleware.DebugToolbarMiddleware',)
         if USE_DEBUG_TOOLBAR else ()) + (

    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'gobotany.middleware.SmartAppendSlashMiddleware',
)

APPEND_SLASH = False
SMART_APPEND_SLASH = True
ROOT_URLCONF = 'gobotany.urls'
INTERNAL_IPS = ('127.0.0.1',)
MEDIA_ROOT = os.path.join(THIS_DIRECTORY, 'media')
MEDIA_URL = '/media/'
SESSION_COOKIE_AGE = 2 * 24 * 60 * 60  # two days

SOUTH_MIGRATION_MODULES = {
    'registration': 'registration.south_migrations',
}

# Static files (CSS, JavaScript, images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_ROOT = (THIS_DIRECTORY)
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(THIS_DIRECTORY, 'static'),
)

# https://docs.djangoproject.com/en/dev/topics/i18n/timezones/#time-zones-faq
TIME_ZONE = 'America/New_York'
USE_TZ = True

# For django-haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr',
        'TIMEOUT': 20,  # Longer than default timeout; added for indexing
        'INCLUDE_SPELLING': True,
        'BATCH_SIZE': 100,
    },
}
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 10
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
# For when we are running on Heroku:
if 'WEBSOLR_URL' in os.environ:
    HAYSTACK_CONNECTIONS['default']['URL'] = os.environ['WEBSOLR_URL']

# For django-facebook-connect
FACEBOOK_LOGIN_REDIRECT = '/plantshare/'
FACEBOOK_SCOPE = 'email'
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')

# For django-registration
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_URL = '/plantshare/accounts/login/'
# To test with this, start a local test email server as follows:
# python -m smtpd -n -c DebuggingServer localhost:1025
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '')
DEFAULT_FROM_EMAIL = 'no-reply@newenglandwild.org'
# SendGrid Heroku add-on configuration
EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME', '')
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', '')
if EMAIL_HOST_USER:
    USE_TLS = True

# For emailconfirmation
EMAIL_CONFIRMATION_DAYS = 3

# For django-recaptcha
if DEV_FEATURES:
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY_DEV', '')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY_DEV', '')
else:
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')
RECAPTCHA_USE_SSL = True

# For static Google Maps (dynamic ones use a different key, in google_maps.js)
GMAPS_STATIC_KEY = os.environ.get('GOBOTANY_GMAPS_KEY_STATIC', '')

TINYMCE_JS_URL = "tiny_mce/tiny_mce.js"

# Use memcached for caching if Heroku provides MEMCACHIER_SERVERS, or if a
# developer runs us locally with that environment variable set.

if 'MEMCACHIER_SERVERS' in os.environ:
    os.environ['MEMCACHE_SERVERS'] = os.environ.get('MEMCACHIER_SERVERS', '').replace(',', ';')
    os.environ['MEMCACHE_USERNAME'] = os.environ.get('MEMCACHIER_USERNAME', '')
    os.environ['MEMCACHE_PASSWORD'] = os.environ.get('MEMCACHIER_PASSWORD', '')

    CACHES = {
      'default': {
        'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',
        'TIMEOUT': 500,
        'BINARY': True,
        'OPTIONS': { 'tcp_nodelay': True }
      }
    }

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
    AWS_S3_SECURE_URLS = True

IS_AWS_AUTHENTICATED = 'test' not in sys.argv and (
    AWS_ACCESS_KEY_ID != 'readonly' and
    AWS_SECRET_ACCESS_KEY != 'readonly'
    )

# Enable gunicorn sub-command if gunicorn is available.

try:
    import gunicorn
except ImportError:
    pass
else:
    INSTALLED_APPS.append('gunicorn')


REGION_NAME = 'New England'
STATE_NAMES = {
    'ct': u'Connecticut',
    'ma': u'Massachusetts',
    'me': u'Maine',
    'nh': u'New Hampshire',
    'ri': u'Rhode Island',
    'vt': u'Vermont',
    }

CONTENT_IMAGE_LOCATIONS = {
    u'pilegroup': 'taxon-images',
    u'pile': 'taxon-images',
    u'family': lambda i,f: 'taxon-images/%s/%s'%(i.content_object.name, f),
    u'genus': lambda i,f: 'taxon-images/%s/%s'%(i.content_object.family.name,
                                                f),
    u'taxon': lambda i,f: 'taxon-images/%s/%s'%(i.content_object.family.name,
                                                f),
}

SITES = {
    'LOCAL': 1,
    'DEV': 2,
    'PROD': 3,
}

SITE_ID = SITES['LOCAL']
if IN_PRODUCTION:
	if DEV_FEATURES:
		SITE_ID = SITES['DEV']
	else:
		SITE_ID = SITES['PROD']

# Name of the Group to which PlantShare users belong once they have
# agreed to the PlantShare Terms of Agreement.
AGREED_TO_TERMS_GROUP = 'Agreed to PlantShare Terms'

ADMINS = (('Go Botany Dev', 'gobotanydev@newenglandwild.org'), )

# https://docs.djangoproject.com/en/1.5/ref/settings/#secure-proxy-ssl-header
# Use SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if IN_PRODUCTION:
    # https://docs.djangoproject.com/en/1.5/topics/security/#ssl-https
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
