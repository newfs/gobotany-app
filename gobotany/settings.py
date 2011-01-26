import os
import sys
try:
    from postgis_paths import GDAL_LIBRARY_PATH, GEOS_LIBRARY_PATH
except ImportError:  # since it does not exist under the Go Botany! buildout
    pass

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
            'HOST': '/tmp',
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
    'appmedia',

    'haystack',
    'sorl.thumbnail',
    'tinymce',
    ]
MIDDLEWARE_CLASSES = (
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

# XXX: It would be nice if we could put this into the buildout var
# instead of the package
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')
STATIC_URL = '/static/'
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'admin-media')
ADMIN_MEDIA_PREFIX = '/admin-media/'
THUMBNAIL_BASEDIR = 'content-thumbs'

DEBUG_DOJO = bool(int(os.environ.get('DEBUG_DOJO', False)))

HAYSTACK_SITECONF = 'gobotany.simplekey.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8983/solr'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 10

TINYMCE_JS_URL = MEDIA_URL + "tinymce/tiny_mce/tiny_mce.js"
TINYMCE_JS_ROOT = os.path.join(MEDIA_ROOT, "tinymce/tiny_mce")

# For partner sites, the request hostname will indicate the site.
MONTSHIRE_HOSTNAME_SUBSTRING = ':8001'  # Just look for a port number for now
