from distutils.core import setup
from setuptools import find_packages

requirements = [
    'django==2.2.17',

    'Pillow==7.2.0',
    'bleach==3.1.5',
    'cssselect',
    'django-debug-toolbar==1.5',
    'django-extensions==2.2.1',
    'django-haystack==2.8.0', # note: versions > 2.7.0 may result in bugs: #717
    'django-haystack-panel==0.2.1',
    'django-imagekit==4.0.2',
    'django-tinymce==2.6.0',
    'inflect',
    'lxml==4.4.1',
    'psycopg2==2.8.5',
    'python-memcached',
    'pytz',
    'tablib==0.12.1',
    'xlrd',

    # The way we use pysolr introduces an extra dependency

    'pysolr==3.7.0',
    'beautifulsoup4==4.8.0',

    # Memcached on Heroku
#
#    'django-pylibmc==0.6.1',
#    'pylibmc==1.5.2',

    # Login and registration

    'django-registration==3.1.1',
    'django-user-accounts==2.1.0', # for changing email addresses

    # For storing images on S3.

    'boto==2.49.0',
    'django-storages==1.7.2',
    'requests',

    # Heroku and deployment

    'gunicorn==20.0.4',
    'newrelic',
    's3cmd',
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
