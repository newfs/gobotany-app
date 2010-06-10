import os
import sys

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
    'gobotany',
    'piston',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.contenttypes',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'cms',
    'menus',
    'cms.plugins.text',
    'cms.plugins.picture',
    'cms.plugins.link',
    'cms.plugins.file',
    'cms.plugins.snippet',
    'cms.plugins.googlemap',
    'mptt',
    'publisher',
    'appmedia',
    ]
MIDDLEWARE_CLASSES = (
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.media.PlaceholderMediaMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = (
        "django.core.context_processors.auth",
        "django.core.context_processors.i18n",
        "django.core.context_processors.request",
        "django.core.context_processors.media",
        "cms.context_processors.media",
)
CMS_TEMPLATES = (
        ('base_cms.html', gettext('default')),
)
CMS_TEMPLATE_INHERITANCE = True
CMS_LANGUAGES = (
    ('en', gettext('English')),
)
ROOT_URLCONF = 'gobotany.urls'
DEBUG = True

# XXX: It would be nice if we could put this into the buildout var
# instead of the package
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'admin-media')
ADMIN_MEDIA_PREFIX = '/admin-media/'

DEBUG_DOJO_ROOT = os.path.join(os.path.dirname(__file__),
                               '..', '..', '..', 'dojo')
