import os

gettext = lambda s: s

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'gobotany'
DATABASE_HOST = '/tmp'
DATABASE_USER = ''
DATABASE_PASSWORD = ''
INSTALLED_APPS = [
    'gobotany',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.contenttypes',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'cms',
    'cms.plugins.text',
    'cms.plugins.picture',
    'cms.plugins.link',
    'cms.plugins.file',
    'cms.plugins.snippet',
    'cms.plugins.googlemap',
    'mptt',
    'publisher',
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
        ('base.html', gettext('default')),
        ('2col.html', gettext('2 Column')),
        ('3col.html', gettext('3 Column')),
        ('extra.html', gettext('Some extra fancy template')),
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
