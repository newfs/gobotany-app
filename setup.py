from distutils.core import setup
from setuptools import find_packages

requirements = [
    'django==1.11.18',

    'Pillow==3.3.1',
    'bleach==1.4.3',
    'cssselect',
    'django-debug-toolbar==1.5',
    'django-haystack==2.7.dev0', # versions beyond this result in bugs: #717
    'django-haystack-panel==0.2.1',
    'django-imagekit==4.0.2',
    'django-tinymce==2.6.0',
    'inflect',
    'lxml==3.5.0',
    'psycopg2==2.7.3.2',
    'python-memcached',
    'pytz',
    'tablib==0.12.1',
    'xlrd',

    # The way we use pysolr introduces an extra dependency

    'pysolr==3.7.0',
    'BeautifulSoup==3.2.1',

    # Memcached on Heroku

    'django-pylibmc==0.6.1',
    'pylibmc==1.5.1',

    # Login and registration

    'django-recaptcha==1.4.0',
    'django-registration==2.1.1',
    'django-user-accounts==2.1.0', # for changing email addresses

    # For storing images on S3.

    'boto==2.39.0',
    'django-storages==1.4.1',
    'requests',

    # Heroku and deployment

    'gunicorn==19.9.0',
    'newrelic',
    's3cmd',
    'django-sslify>=0.2',
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
