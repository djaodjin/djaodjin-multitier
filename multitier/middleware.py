# Copyright (c) 2015, Djaodjin Inc.
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


import logging, re, os, sys
import gettext as gettext_module

from django.conf import settings as django_settings
from django.db import connections
from django.db.models import Q
from django.db.utils import DEFAULT_DB_ALIAS
from django.http import Http404
from django.utils.translation.trans_real import _active
from django.utils._os import upath

from . import settings, get_site_model
from .models import Site
from .locals import clear_cache, set_current_site
from .urlresolvers import SiteCode

LOGGER = logging.getLogger(__name__)

def as_provider_db(db_name):
    """
    Returns a dictionnary that can be used to initialized a database
    connection to the site (streetside) database.
    """
    provider_db = \
        connections.databases[DEFAULT_DB_ALIAS].copy()
    default_db_name = provider_db['NAME']
    provider_db.update({'NAME':db_name})
    if provider_db['ENGINE'].endswith('sqlite3'):
        # HACK to set absolute paths (used in development environments)
        candidates = [os.path.join(dir_path, db_name + '.sqlite')
            for dir_path in [os.path.dirname(default_db_name)]
                       + settings.DEBUG_SQLITE3_PATHS]
        for candidate_db in candidates:
            if os.path.exists(candidate_db):
                provider_db['NAME'] = candidate_db
                LOGGER.debug("multitier: using database '%s'", candidate_db)
                return provider_db
        LOGGER.error("multitier: cannot find db '%s'", db_name)
    return provider_db


class SiteMiddleware(object):

    def __init__(self):
        pass

    @staticmethod
    def as_candidate_site(request):
        """
        Returns a ``Site`` based on the request host.
        """
        site = None
        candidate = None
        path_prefix = ''
        host = request.get_host().split(':')[0].lower()
        if len(django_settings.ALLOWED_HOSTS) > 0:
            domain = django_settings.ALLOWED_HOSTS[0]
            if domain.startswith('.'):
                domain = domain[1:]
            look = re.match(r'^((?P<subdomain>\S+)\.)?%s(?::.*)?$' % domain,
                host)
            if look and look.group('subdomain'):
                candidate = look.group('subdomain')
#                LOGGER.debug("multitier: found subdomain candidate: %s",
#                    candidate)
        look = re.match(r'^/(?P<path_prefix>[a-zA-Z0-9\-]+).*', request.path)
        # no trailing '/' is OK here.
        if look:
            path_prefix = look.group('path_prefix')
        if not candidate:
            # It is either a subdomain or a path_prefix. Trying both
            # match one after the other will always override the candidate.
            if path_prefix:
                candidate = path_prefix
#                LOGGER.debug("multitier: found path_prefix candidate: '%s'",
#                    candidate)
            else:
                candidate = django_settings.APP_NAME
        try:
            queryset = get_site_model().objects.filter(Q(domain=host)
                | Q(slug=candidate) | Q(slug=django_settings.APP_NAME)
            ).order_by('-pk')
            if not queryset.exists():
                raise Site.DoesNotExist #pylint: disable=raising-bad-type
            site = queryset.first()
            if site and site.slug != path_prefix:
                path_prefix = ''
        except Site.DoesNotExist:
            raise Http404(
                "%s nor %s could be found." % (host, django_settings.APP_NAME))
        LOGGER.debug("multitier: access site '%s' with prefix '%s'",
            site, path_prefix)
        return site, path_prefix


    def process_request(self, request):
        """
        Adds a ``client`` attribute to the ``request`` parameter.
        """
        clear_cache()
        site, path_prefix = self.as_candidate_site(request)

        # Dynamically update the db used for auth and saas.
        if site.db_name:
            LOGGER.debug("multitier: connect to db '%s'", site.db_name)
            if not site.db_name in connections.databases:
                connections.databases[site.db_name] = as_provider_db(
                    site.db_name)
        else:
            LOGGER.debug("multitier: use 'default' db")

        # This is where you would typically override ``request.urlconf``
        # based on the ``Site``.

        # Set thread locals.
        # 1. First the site such that the we route requests for ``Site``
        # instances to the correct database.
        # 2. Then we hack into the translation module to get
        # django.core.urlresolvers to play nicely with our url scheme
        # with regards to the active site.
        set_current_site(site, path_prefix)
        globalpath = os.path.join(os.path.dirname(
                upath(sys.modules[django_settings.__module__].__file__)),
                'locale')
        _active.value = gettext_module.translation(
            'django', globalpath, class_=SiteCode)
        return None

