from distutils.core import setup
from setuptools import find_packages

requirements = [
    'django==1.7.9',

    'Pillow==2.4.0',
    'South==1.0',
    'cssselect',
    'django-debug-toolbar==1.3.0',
    'django-haystack==1.2.7',
    'django-imagekit==3.0.2',
    'django-tinymce',
    'lxml',
    'psycopg2>=2.3',
    'python-memcached',
    'pytz',
    'tablib==0.9.11',
    'xlrd',

    # The way we use pysolr introduces an extra dependency

    'pysolr==2.0.15',
    'BeautifulSoup==3.2.1',

    # Memcached on Heroku

    'django-pylibmc-sasl==0.2.4',
    'pylibmc==1.2.3',

    # Login and registration

    'django-email-confirmation==0.2',
    'django-facebook-connect>=1.0.2',
    'django-recaptcha==1.0.4',
    'django-registration-redux==1.2',

    # For storing images on S3.

    'boto==2.2.2',
    'django-storages==1.1.4',
    'requests',

    # Heroku and deployment

    'gunicorn==0.17.2',
    'newrelic',
    's3cmd',
    'django-sslify>=0.2',
    ]

dependency_links = [
    'git+https://github.com/noamsu/django-facebook-connect'
    + '#egg=django-facebook-connect-1.0.2',
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
