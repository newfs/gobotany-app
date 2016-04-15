from distutils.core import setup
from setuptools import find_packages

requirements = [
    'django==1.8.12',

    'Pillow==2.4.0',
    'cssselect',
    'django-debug-toolbar==1.3.2',
    'django-haystack==2.4.0',
    'django-haystack-panel==0.2.1',
    'django-imagekit==3.2.6',
    'django-tinymce==1.5.3',
    'inflect',
    'lxml==3.5.0',
    'psycopg2>=2.4.5',
    'python-memcached',
    'pytz',
    'tablib==0.9.11',
    'xlrd',

    # The way we use pysolr introduces an extra dependency

    'pysolr==3.4.0',
    'BeautifulSoup==3.2.1',

    # Memcached on Heroku

    'django-pylibmc-sasl==0.2.4',
    'pylibmc==1.2.3',

    # Login and registration

    'django-email-confirmation==0.2',
    'django-recaptcha==1.0.4',
    'django-registration-redux==1.2',

    # For storing images on S3.

    'boto==2.39.0',
    'django-storages==1.4.1',
    'requests',

    # Heroku and deployment

    'gunicorn==0.17.2',
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
