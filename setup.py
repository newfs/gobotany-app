import os
import subprocess
import sys
from distutils.core import setup
from setuptools import find_packages

if 'TOX' in os.environ:
    # Be kind to the poor developer: when this is being run locally on a
    # developer machine using "tox", only proceed with a full install
    # attempt if the necessary system-wide requirements are in place.
    try:
        subprocess.check_call(['bash', 'dev/check-dependencies'])
    except subprocess.CalledProcessError:
        sys.exit(2)

requirements = [
    'django==1.4',

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
    'xlrd',

    # The way we use pysolr introduces an extra dependency

    'pysolr==2.0.15',
    'BeautifulSoup==3.2.1',

    # Memcached on Heroku

    'django-pylibmc-sasl==0.2.4',
    'pylibmc==1.2.2',

    # Login and registration

    'django-facebook-connect>=1.0.2',
    'django-recaptcha==0.0.4',
    'django-registration==0.8',

    # For storing images on S3.

    'boto==2.2.2',
    'django-storages==1.1.4',
    'requests',

    # Heroku and deployment

    'gunicorn',
    'newrelic',
    's3cmd',
    ]

dependency_links = [
    'git+https://github.com/jrrickerson/django-facebook-connect'
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
