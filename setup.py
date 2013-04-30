from distutils.core import setup
from setuptools import find_packages

requirements = [
    'django==1.5',

    'PIL',
    'South==0.7.6',
    'cssselect',
    'django-debug-toolbar',
    'django-haystack==1.2.7',
    'django-imagekit==2.0.2',
    'django-piston==0.2.2',
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

    'django-facebook-connect>=1.0.2',
    'django-recaptcha==0.0.6',
    # Installed in a separate step pending Django dependency issues
    'django-registration==0.9b1',

    # For storing images on S3.

    'boto==2.2.2',
    'django-storages==1.1.4',
    'requests',

    # Heroku and deployment

    'gunicorn==0.17.2',
    'newrelic',
    's3cmd',
    ]

dependency_links = [
    'git+https://github.com/jrrickerson/django-facebook-connect'
    + '#egg=django-facebook-connect-1.0.2',
    'https://bitbucket.org/alper/django-registration/get/tip.tar.gz'
    + '#egg=django-registration-0.9b1'
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
