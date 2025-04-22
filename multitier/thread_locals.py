# Copyright (c) 2025, Djaodjin Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging, os

from django.db import connections
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.encoding import iri_to_uri

from . import settings
from .compat import python_2_unicode_compatible, reverse, urljoin, urlparse

try:
    from threading import local
except ImportError:
    #pylint: disable=import-error,no-name-in-module
    from django.utils._threading_local import local

_thread_locals = local() #pylint: disable=invalid-name

LOGGER = logging.getLogger(__name__)


@python_2_unicode_compatible
class CurrentSite(object):

    def __init__(self, site, path_prefix,
                 default_scheme='http', default_host='localhost'):
        self.db_object = site
        self.path_prefix = path_prefix
        self.default_scheme = default_scheme
        self.default_host = default_host

    def __getattr__(self, name):
        return getattr(self.db_object, name)

    def __str__(self):
        return self.db_object.__str__()

    def as_absolute_uri(self, location='/'):
        parts = urlparse(location)
        if parts.scheme and parts.netloc:
            # If we already have an absolute URI then we have not processing
            # to do and just return it "as is".
            return location

        if self.db_object.domain:
            host = self.db_object.domain
        else:
            host = self.default_host
            if self.path_prefix:
                location = location.lstrip('/')
                if location.startswith(self.path_prefix):
                    location = location[len(self.path_prefix):]
                # `lstrip` again In case we removed the path_prefix previously.
                location = urljoin('/%s/' % self.path_prefix,
                    location.lstrip('/'))
        return iri_to_uri('%(scheme)s://%(host)s%(path)s' % {
            'scheme': self.default_scheme, 'host': host, 'path': location})


def as_provider_db(db_name, db_host=None, db_port=None):
    """
    Returns a dictionnary that can be used to initialized a database
    connection to the a site-specific database.
    """
    provider_db = connections.databases[DEFAULT_DB_ALIAS].copy()
    default_db_name = provider_db['NAME']
    provider_db.update({'NAME':db_name})
    if db_host:
        provider_db.update({'HOST':db_host})
    if db_port:
        provider_db.update({'PORT':db_port})
    if provider_db['ENGINE'].endswith('sqlite3'):
        # HACK to set absolute paths (used in development environments)
        candidates = [os.path.join(dir_path, db_name + '.sqlite')
            for dir_path in [os.path.dirname(default_db_name)]
                       + settings.DEBUG_SQLITE3_PATHS]
        # When the sqlite database file does not yet exists, we want
        # to default to a db file in the same directory as default,
        # not a file in the current directory.
        provider_db['NAME'] = candidates[0]
        for candidate_db in candidates:
            if os.path.exists(candidate_db):
                provider_db['NAME'] = candidate_db
                LOGGER.debug("multitier: using database '%s'", candidate_db)
                return provider_db
        LOGGER.error("multitier: cannot find db '%s'", db_name)
    return provider_db


def cache_provider_db(db_name, db_host=None, db_port=None):
    if not db_name:
        return None
    if not db_name in connections.databases:
        connections.databases[db_name] = as_provider_db(db_name,
            db_host=db_host, db_port=db_port)
    return connections.databases[db_name]


def clear_cache():
    try:
        del _thread_locals.site
    except AttributeError:
        pass


def get_current_site():
    """
    Returns the ``Site`` associated to the thread request.
    """
    return getattr(_thread_locals, 'site', None)


def get_path_prefix():
    """
    Returns the prefix every URL paths is prefixed with.
    """
    site = get_current_site()
    if site:
        return site.path_prefix
    return ""

# SMTP connection
# ---------------
def get_email_connection(site=None):
    """
    Returns a connection to the e-mail server for the site.
    """
    if not site:
        site = get_current_site()
    return site.get_email_connection()


def get_default_from_email():
    site = get_current_site()
    email_default_from = ""
    email_host_user = ""
    if site:
        email_default_from = site.email_default_from
        email_host_user = site.email_host_user
    if email_default_from:
        return email_default_from
    if email_host_user and '@' in email_host_user:
        return email_host_user
    return ""

# User and profile accounts settings
# ----------------------------------
def get_authentication_override():
    """
    Returns the authentication settings for the current site.
    """
    site = get_current_site()
    if site:
        return site.authentication
    return 0


def get_registration_type():
    """
    Returns the registration settings for the current site.
    """
    site = get_current_site()
    if site:
        return site.registration
    return 0


def get_registration_requires_recaptcha():
    site = get_current_site()
    if site:
        return site.registration_requires_recaptcha
    return False


def get_contact_requires_recaptcha():
    site = get_current_site()
    if site:
        return site.contact_requires_recaptcha
    return False


def get_recaptcha_pub_key():
    site = get_current_site()
    value = ""
    if site:
        value = site.recaptcha_pub_key
    if not value:
        return ""
    return value


def get_recaptcha_priv_key():
    site = get_current_site()
    value = ""
    if site:
        try:
            value = site.recaptcha_priv_key
        except: #pylint:disable=bare-except
            # might not be able to decrypt database field.
            LOGGER.error("cannot read recaptcha_priv_key for site '%s'", site)
    if not value:
        return ""
    return value


def get_social_auth_azuread_oauth2_key():
    site = get_current_site()
    value = ""
    if site:
        value = site.social_auth_azuread_pub_key
    if not value:
        return ""
    return value


def get_social_auth_azuread_oauth2_secret():
    site = get_current_site()
    value = ""
    if site:
        try:
            value = site.social_auth_azuread_priv_key
        except: #pylint:disable=bare-except
            # might not be able to decrypt database field.
            LOGGER.error(
                "cannot read social_auth_azuread_priv_key for site '%s'", site)
    if not value:
        return ""
    return value


def get_social_auth_github_key():
    site = get_current_site()
    value = ""
    if site:
        value = site.social_auth_github_pub_key
    if not value:
        return ""
    return value


def get_social_auth_github_secret():
    site = get_current_site()
    value = ""
    if site:
        try:
            value = site.social_auth_github_priv_key
        except: #pylint:disable=bare-except
            # might not be able to decrypt database field.
            LOGGER.error(
                "cannot read social_auth_github_priv_key for site '%s'", site)
    if not value:
        return ""
    return value


def get_social_auth_google_oauth2_key():
    site = get_current_site()
    value = ""
    if site:
        value = site.social_auth_google_pub_key
    if not value:
        return ""
    return value


def get_social_auth_google_oauth2_secret():
    site = get_current_site()
    value = ""
    if site:
        try:
            value = site.social_auth_google_priv_key
        except: #pylint:disable=bare-except
            # might not be able to decrypt database field.
            LOGGER.error(
                "cannot read social_auth_google_priv_key for site '%s'", site)
    if not value:
        return ""
    return value

# street address auto-complete (Google Places)
# --------------------------------------------
def get_google_api_key():
    site = get_current_site()
    value = ""
    if site:
        try:
            value = site.google_api_key
        except: #pylint:disable=bare-except
            # might not be able to decrypt database field.
            LOGGER.error("cannot read google_api_key for site '%s'", site)
    if not value:
        return ""
    return value


# Payment processor
# -----------------
def get_processor_use_platform_keys():
    site = get_current_site()
    if site:
        return site.processor_is_platform
    return False


def get_processor_pub_key():
    site = get_current_site()
    value = ""
    if site:
        value = site.processor_pub_key
    if not value:
        return ""
    return value


def get_processor_priv_key():
    site = get_current_site()
    value = ""
    if site:
        try:
            value = site.processor_priv_key
        except: #pylint:disable=bare-except
            # might not be able to decrypt database field.
            LOGGER.error("cannot read processor_priv_key for site '%s'", site)
    if not value:
        return ""
    return value


def get_processor_client_id():
    site = get_current_site()
    value = ""
    if site:
        value = site.processor_client_key
    if not value:
        return ""
    return value


def get_processor_connect_callback_url():
    site = get_current_site()
    value = ""
    if site:
        value = site.connect_callback_url
    if not value:
        return ""
    return value


def get_enables_processor_test_keys():
    site = get_current_site()
    if site:
        return site.enables_processor_test_keys
    return False


def get_processor_test_pub_key():
    site = get_current_site()
    value = ""
    if site:
        value = site.processor_test_pub_key
    if not value:
        return ""
    return value


def get_processor_test_priv_key():
    site = get_current_site()
    value = ""
    if site:
        try:
            value = site.processor_test_priv_key
        except: #pylint:disable=bare-except
            # might not be able to decrypt database field.
            LOGGER.error(
                "cannot read processor_test_priv_key for site '%s'", site)
    if not value:
        return ""
    return value


def get_processor_test_client_id():
    site = get_current_site()
    value = ""
    if site:
        value = site.processor_test_client_key
    if not value:
        return ""
    return value


def get_processor_test_connect_callback_url():
    site = get_current_site()
    value = ""
    if site:
        value = site.connect_test_callback_url
    if not value:
        return ""
    return value


# Notification workflow settings
# ------------------------------
def get_notification_webhook_url():
    site = get_current_site()
    value = ""
    if site:
        value = site.notification_webhook_url
    if not value:
        return ""
    return value


def get_notification_email_disabled():
    site = get_current_site()
    if site:
        return site.notification_email_disabled
    return False


def set_current_site(site, path_prefix,
        default_scheme='http', default_host='localhost', request=None):
    # Dynamically update the db used for auth and saas.
    if site.db_name:
        LOGGER.debug(
            "multitier: access site '%s' with prefix '%s', connect to db '%s'",
            site, path_prefix, site.db_name)
        if not site.db_name in connections.databases:
            cache_provider_db(site.db_name,
                db_host=site.db_host, db_port=site.db_port)
    else:
        LOGGER.debug(
            "multitier: access site '%s' with prefix '%s',"\
            " connect to db 'default'", site, path_prefix)

    prev_site = None
    prev_path_prefix = None
    if (hasattr(_thread_locals, 'site')
        and isinstance(_thread_locals.site, CurrentSite)):
        prev_site = _thread_locals.site.db_object
        prev_path_prefix = _thread_locals.site.path_prefix
        _thread_locals.site.db_object = site
        _thread_locals.site.path_prefix = path_prefix
    else:
        _thread_locals.site = CurrentSite(site, path_prefix,
            default_scheme=default_scheme, default_host=default_host)

    if request is not None:
        request.site = _thread_locals.site
        request.urls = {}
        for url_name in settings.DEFAULT_URLS:
            request.urls.update({url_name: reverse(url_name)})
    return (prev_site, prev_path_prefix)
