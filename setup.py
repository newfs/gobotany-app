from distutils.core import setup
from setuptools import find_packages

requirements = [
    'django==3.1.14',

    'Pillow==9.1.1',
    'bleach==3.3.0',
    'cssselect',
    'django-debug-toolbar==3.2.1',
    'django-extensions==3.1.2',

    'django-haystack==3.0',
    # There is now a debug toolbar panel included with Haystack, but
    # unfortunately as of version 3.0 it needs fixes to work. The old
    # panel we used, django-haystack-panel, is a retired project and
    # no longer shows the Haystack queries, so it was removed.

    'django-imagekit==4.0.2',
    'django-tinymce==3.4.0',
    'inflect',
    'lxml==4.9.1',
    'psycopg2==2.9.2',
    'python-memcached',
    'pytz',
    'tablib==0.12.1',
    'xlrd',

    # The way we use pysolr introduces an extra dependency

    'pysolr==3.9.0',
    'beautifulsoup4==4.9.3',

    # Memcached on Heroku

    'django-pylibmc==0.6.1',
    'pylibmc==1.5.2',

    # Login and registration

    'django-registration==3.1.2',
    'django-user-accounts==3.0.2', # for changing email addresses

    # For storing images on S3.

    'boto==2.49.0',
    'django-storages==1.7.2',
    'requests',

    # Heroku and deployment

    'gunicorn==20.0.4',
    'newrelic',
    'python-magic==0.4.24',
    's3cmd==2.2.0',
    ]

dependency_links = [
    ]

packages = find_packages()
package_data = {package: ['templates/*.*', 'templates/*/*.*']
                for package in packages}
package_data['gobotany'].append('static/*.*')
package_data['gobotany'].append('static/*/*.*')
package_data['gobotany'].append('static/*/*/*.*')
package_data['gobotany'].append('static/*/*/*/*.*')
package_data['gobotany.api'].append('testdata/*.*')
package_data['gobotany.core'].append('image_categories.csv')
package_data['gobotany.core'].append('testdata/*.*')

setup(
    name='gobotany',
    py_modules=['bulkup'],
    packages=packages,
    package_data=package_data,
    install_requires=requirements,
    dependency_links=dependency_links,
    )
