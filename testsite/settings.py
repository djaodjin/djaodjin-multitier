"""
Django settings for testsite project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APP_NAME = os.path.basename(BASE_DIR)

def load_config(confpath):
    '''
    Given a path to a file, parse its lines in ini-like format, and then
    set them in the current namespace.
    '''
    # todo: consider using something like ConfigObj for this:
    # http://www.voidspace.org.uk/python/configobj.html
    import re, sys
    if os.path.isfile(confpath):
        sys.stderr.write('config loaded from %s\n' % confpath)
        with open(confpath) as conffile:
            line = conffile.readline()
            while line != '':
                if not line.startswith('#'):
                    look = re.match(r'(\w+)\s*=\s*(.*)', line)
                    if look:
                        value = look.group(2) \
                            % {'LOCALSTATEDIR': BASE_DIR + '/var'}
                        try:
                            # Once Django 1.5 introduced ALLOWED_HOSTS (a tuple
                            # definitely in the site.conf set), we had no choice
                            # other than using eval. The {} are here to restrict
                            # the globals and locals context eval has access to.
                            # pylint: disable=eval-used
                            setattr(sys.modules[__name__],
                                    look.group(1).upper(), eval(value, {}, {}))
                        except StandardError:
                            raise
                line = conffile.readline()
    else:
        sys.stderr.write('warning: config file %s does not exist.\n' % confpath)

load_config(os.path.join(BASE_DIR, 'credentials'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django_extensions',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'multitier',
    'testsite',
)

MIDDLEWARE_CLASSES = (
    'multitier.middleware.SiteMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'testsite.urls'

WSGI_APPLICATION = 'testsite.wsgi.application'

# Templates
# ---------
TEMPLATE_DEBUG = True

# Django 1.7 and below
TEMPLATE_LOADERS = (
    'multitier.template_loader.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'multitier.context_processors.site',
    'multitier.context_processors.features_debug'
)

TEMPLATE_DIRS = (
    BASE_DIR + '/testsite/templates',
)

# Django 1.8+
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'OPTIONS': {
            'context_processors': [proc.replace(
                'django.core.context_processors',
                'django.template.context_processors')
                for proc in TEMPLATE_CONTEXT_PROCESSORS],
            'loaders': TEMPLATE_LOADERS},
    },
]

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASE_ROUTERS = ('multitier.routers.SiteRouter',)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite')
    }
}

if os.getenv('MULTITIER_DB_FILE'):
    MULTITIER_DB_FILE = os.getenv('MULTITIER_DB_FILE')
    MULTITIER_DB_NAME = os.path.splitext(
        os.path.basename(MULTITIER_DB_FILE))[0]
    DATABASES.update({MULTITIER_DB_NAME: {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': MULTITIER_DB_FILE,
    }})

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR + '/testsite/media'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_ROOT = BASE_DIR + '/testsite/static'

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'logfile':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'multitier': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
#        'django.db.backends': {
#             'handlers': ['logfile'],
#             'level': 'DEBUG',
#             'propagate': True,
#        },
    }
}

LOGIN_REDIRECT_URL = 'accounts_profile'
