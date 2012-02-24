import urlparse
import os
import sys
import traceback

try:
    import gobotany
except ImportError:
    sys.path[0:0] = [ os.path.dirname(os.path.dirname(os.path.abspath(__file__))) ]
    import gobotany

GOBOTANY_DIR = os.path.dirname(gobotany.__file__)

try:
    from postgis_paths import GDAL_LIBRARY_PATH, GEOS_LIBRARY_PATH
except ImportError:  # since it does not exist under the Go Botany! buildout
    pass

# Make sure that our current directory is a buildout (or at least the
# "bin" directory inside of a buildout), so we can determine where our
# MEDIA and STATIC directories live.

buildout_dir = os.getcwd()
if os.path.basename(buildout_dir) == 'bin':
    buildout_dir = os.path.dirname(buildout_dir)
ls = os.listdir(buildout_dir)
if '.installed.cfg' not in ls:
    # Maybe the path to django.wsgi is the bottom frame?
    frames = traceback.extract_stack()
    wsgi_script = frames[0][0]  # filename of the bottom stack frame
    buildout_dir = os.path.dirname(os.path.dirname(wsgi_script))
    ls = os.listdir(buildout_dir)
if '.installed.cfg' not in ls:
    print >>sys.stderr, (
        '\n'
        'Error: the "gobotany" project must be run from inside a buildout,\n'
        'but your current working directory lacks an ".installed.cfg" file.\n'
        )
    sys.exit(1)

# src/gobotany/media - tinymce
# src/gobotany/static - gobotany/**.js, graphics, *.css, etc
# 
#
# REMOVE src/gobotany/admin-media?

gettext = lambda s: s

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'HOST': '',
            'USER': '',
            'PASSWORD': '',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'gobotany',
            'HOST': '',
            'USER': '',
            'PASSWORD': '',
        }
    }

if 'HEROKU_SHARED_POSTGRESQL_BLACK_URL' in os.environ:

    # For the sake of Heroku.

    os.environ['DATABASE_URL'] = os.environ[
        'HEROKU_SHARED_POSTGRESQL_BLACK_URL']

    # For the sake of scripts running locally on a developer
    # workstation, but with a Heroku database URL provided.  This code
    # is adapted from: http://devcenter.heroku.com/articles/django

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
    'gobotany.mapping',
    'gobotany.plantoftheday',
    'gobotany.search',
    'gobotany.simplekey',
    'piston',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'haystack',
    'tinymce',
    ]
MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'gobotany.middleware.SmartAppendSlashMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.i18n",
        "django.core.context_processors.request",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "gobotany.core.context_processors.dojo",
)

APPEND_SLASH = False
SMART_APPEND_SLASH = True

ROOT_URLCONF = 'gobotany.urls'
DEBUG = True

MEDIA_ROOT = os.path.join(buildout_dir, 'var', 'gobotany-media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(buildout_dir, 'var', 'gobotany-static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [('', os.path.join(GOBOTANY_DIR, 'static'))]
ADMIN_MEDIA_ROOT = os.path.join(buildout_dir, 'var', 'admin')
ADMIN_MEDIA_PREFIX = '/static/admin/'
THUMBNAIL_BASEDIR = 'content-thumbs'
THUMBNAIL_DEBUG = True

SESSION_COOKIE_AGE = 2 * 24 * 60 * 60  # two days

DEBUG_DOJO = bool(int(os.environ.get('DEBUG_DOJO', False)))

HAYSTACK_SITECONF = 'gobotany.simplekey.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8983/solr'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 10
HAYSTACK_SOLR_TIMEOUT = 20  # Longer than default timeout; added for indexing

# For when we are running on Heroku:
if 'WEBSOLR_URL' in os.environ:
    HAYSTACK_SOLR_URL = os.environ['WEBSOLR_URL']

TINYMCE_JS_URL = "tiny_mce/tiny_mce.js"
TINYMCE_JS_ROOT = os.path.join(STATIC_ROOT, "tiny_mce")

# For partner sites, the request hostname will indicate the site.
MONTSHIRE_HOSTNAME_SUBSTRING = ':8001'  # Just look for a port number for now

# Use memcached for caching if Heroku provides MEMCACHE_SERVERS, or if a
# developer runs us locally with that environment variable set.

if 'MEMCACHE_SERVERS' in os.environ:
    CACHES = {'default': {
        'BACKEND': 'django_pylibmc.memcached.PyLibMCCache'
        }}

# Enable S3 filestorage (which we use mostly [entirely?] for images) if
# the user has set the right environment variables.

if 'AWS_STORAGE_BUCKET_NAME' in os.environ:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_SECURE_URLS = False

# Enable gunicorn sub-command if gunicorn is available.

try:
    import gunicorn
except ImportError:
    pass
else:
    INSTALLED_APPS.append('gunicorn')
