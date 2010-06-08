import os

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'gobotany'
DATABASE_HOST = '/tmp'
DATABASE_USER = ''
DATABASE_PASSWORD = ''
INSTALLED_APPS = ['gobotany',
                  'django.contrib.admin',
                  'django.contrib.sessions',
                  'django.contrib.contenttypes']
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
