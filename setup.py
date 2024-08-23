from distutils.core import setup
from setuptools import find_packages

requirements = [
    'django==4.0',

    'Pillow==10.3.0',
    'bleach==5.0.1',
    'cssselect==1.1.0',
    'django-debug-toolbar==3.6.0',
    'django-extensions==3.2.0',

    'django-haystack==3.2.1',
    # There is now a debug toolbar panel included with Haystack, but
    # unfortunately as of version 3.0 it needs fixes to work. The old
    # panel we used, django-haystack-panel, is a retired project and
    # no longer shows the Haystack queries, so it was removed.

    'django-imagekit==5.0.0',
    'django-tinymce==4.1.0',
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
    'pylibmc==1.6.2',

    # Login and registration

    'django-registration==3.3',
    'django-user-accounts==3.2.0', # for changing email addresses

    # For storing images on S3.

    'boto==2.49.0',   # for bin/s3imagecheck.py
    'boto3==1.35.0',   # has replaced boto in the Django app
    'django-storages==1.13.1',
    'requests',

    # Heroku and deployment

    'gunicorn==22.0.0',
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
