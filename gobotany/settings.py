import os
import sys
import traceback

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

INSTALLED_APPS = [
    'gobotany.api',
    'gobotany.core',
    'gobotany.simplekey',
    'piston',

    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'staticfiles',

    'haystack',
    'sorl.thumbnail',
    'tinymce',
    ]
MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = (
        "django.core.context_processors.auth",
        "django.core.context_processors.i18n",
        "django.core.context_processors.request",
        "django.core.context_processors.media",
        "staticfiles.context_processors.static_url",
        "gobotany.core.context_processors.dojo",
)
THUMBNAIL_PROCESSORS = (
    # Default processors
    'sorl.thumbnail.processors.colorspace',
    #'sorl.thumbnail.processors.autocrop',
    'sorl.thumbnail.processors.scale_and_crop',
    'sorl.thumbnail.processors.filters',
)

ROOT_URLCONF = 'gobotany.urls'
DEBUG = True

MEDIA_ROOT = os.path.join(buildout_dir, 'var', 'gobotany-media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(buildout_dir, 'var', 'gobotany-static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [('', os.path.join(GOBOTANY_DIR, 'static'))]
ADMIN_MEDIA_ROOT = os.path.join(buildout_dir, 'var', 'admin')
ADMIN_MEDIA_PREFIX = '/admin-media/'
THUMBNAIL_BASEDIR = 'content-thumbs'

SESSION_COOKIE_AGE = 2 * 24 * 60 * 60  # two days

DEBUG_DOJO = bool(int(os.environ.get('DEBUG_DOJO', False)))

HAYSTACK_SITECONF = 'gobotany.simplekey.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8983/solr'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 10

TINYMCE_JS_URL = "tiny_mce/tiny_mce.js"
TINYMCE_JS_ROOT = os.path.join(STATIC_ROOT, "tiny_mce")

# For partner sites, the request hostname will indicate the site.
MONTSHIRE_HOSTNAME_SUBSTRING = ':8001'  # Just look for a port number for now
