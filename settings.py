"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from collections import OrderedDict

import django
from split_settings.tools import include, optional

include(
    '/etc/source_optics/conf.d/*.py',
    optional('local_settings.py')
)

#os.environ.setdefault("DJANGO_SETTINGS_MODULE", __file__)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '8p-v&-27ltkxkt4n8*fax#65qa3z1g-^%^^yvqe1^f=9mfs$(6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'source_optics',
    'django_tables2',
    'rest_framework',
    'django_filters'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
# add to /etc/source_optics/conf.d/database.py

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

TEMPLATE_CONTEXT_PROCESSORS = (
  "django.core.context_processors.request",
  "django.core.context_processors.auth",
  "django.core.context_processors.debug",
  "django.core.context_processors.i18n",
  "thetrailbehind.context_processors.canonical_url",
  "thetrailbehind.context_processors.gmapkey",
)

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/source_optics/static/'

# should we record changes for all files in each commit?
#
# This is useful for more advanced file trend analysis,
# but will add A LOT more data and require more scan time
# disabled by default
RECORD_FILE_CHANGES = False

# The location of the symmetric key for password encryption
# should be created in init
SYMMETRIC_SECRET_KEY = '/etc/source_optics/cred.key'

# maximum number of threads to launch per concurrent task
# used in the stat aggregator
#
# None lets django automatically select a count
MAX_THREAD_COUNT = None

# Django unit tests can be run as parallel, but this causes problems with
# lingering postgres connections. use the concurrent flag to disable
# multi-threaded aggregation so that the unit tests behave
#
#   hopefully this will go away eventually
MULTITHREAD_AGGREGATE = False

# the threshold for number of commits at which to print
# some dots as a status update. This is done in checkout.py
DOTS_THRESHOLD = 1000
# the number of columns before we line break
DOTS_WIDTH = 10


REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}


PLUGIN_SEARCH_PATH = []

PLUGIN_CONFIGURATION = dict(
    secrets=OrderedDict(
        basic="source_optics.plugins.secrets.cloak_v1"
    ),
)

SCANNER_LOCK_FILE = "/etc/source_optics/scanner.lock"

# this is the default for git checkouts made by the program
CHECKOUT_DIRECTORY = "/tmp/source_optics"

# ===========================
# APP PREFERENCES

# pull new code from repos if not pulled in N minutes, 0 = always pull
PULL_THRESHOLD = 0
