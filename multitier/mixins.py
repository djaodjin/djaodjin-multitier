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

from django.shortcuts import get_object_or_404

from . import settings
from .compat import get_model_class, import_string
from .thread_locals import cache_provider_db, get_current_site
from .utils import get_site_model
from .compat import urlparse


def is_localhost(hostname):
    return bool(
        hostname.startswith('localhost') or hostname.startswith('127.0.0.1'))


def build_absolute_uri(location='/', request=None, site=None,
                       with_scheme=True, force_subdomain=False):
    """
    Builds an absolute URL for path *location* on *site*.

    It is sometimes useful to force subdomains URL. For example when DNS is not
    yet setup and we still want to be able to access the newly created site.

    If *force_subdomain* is ``True``, the site.domain field is not
    used, regardless of its value (valid or null). By default site.domain
    is used when present.
    """
    parts = urlparse(location)
    if parts.scheme and parts.netloc:
        # If we already have an absolute URI then we have not processing
        # to do and just return it "as is".
        return location

    if site is None:
        site = request.site if hasattr(request, 'site') else get_current_site()
    else:
        site_model = get_site_model()
        if not isinstance(site, site_model):
            try:
                site = site_model.objects.get(slug=site)
            except site_model.DoesNotExist:
                site = None
    actual_domain = settings.DEFAULT_DOMAIN
    if request:
        actual_domain = request.get_host()
    if site:
        if site.domain and not force_subdomain:
            actual_domain = site.domain
        else:
            subdomain = site.as_subdomain()
            is_path_prefix = site.is_path_prefix
            force_path_prefix = False
            base_domain = settings.DEFAULT_DOMAIN
            if request:
                base_domain = request.get_host()
                if is_localhost(base_domain):
                    force_path_prefix = True
            if subdomain:
                if not (force_path_prefix or is_path_prefix):
                    actual_domain = '%s.%s' % (subdomain, base_domain)
                elif not location.startswith('/%s/' % subdomain):
                    # In local development, we force use of path prefixes.
                    # At the same time we don't want to double the path prefix
                    # when it was already added by ``reverse()``.
                    actual_domain = '%s/%s' % (base_domain, subdomain)

    result = "%(domain)s%(path)s" % {'domain': actual_domain, 'path': location}
    if with_scheme:
        scheme = 'http'
        if request and not is_localhost(result):
            scheme = request.scheme
        result = '%s://%s' % (scheme, result)
    return result


class AccountMixin(object):

    account_url_kwarg = settings.ACCOUNT_URL_KWARG

    @property
    def account(self):
        if not hasattr(self, '_account'):
            if settings.ACCOUNT_GET_CURRENT:
                self._account = import_string(settings.ACCOUNT_GET_CURRENT)(
                    self.kwargs.get(self.account_url_kwarg))
            else:
                self._account = get_object_or_404(
                    get_model_class(settings.ACCOUNT_MODEL,
                        "MULTITIER['ACCOUNT_MODEL']"),
                    slug=self.kwargs.get(self.account_url_kwarg, None))
        return self._account


class SiteMixin(AccountMixin):
    """
    Returns a ``Site`` from a URL or the default site if none can be found.
    """
    site_url_kwarg = 'site'

    @property
    def site(self):
        #pylint: disable=access-member-before-definition
        if not hasattr(self, '_site') or self._site is None:
            if self.site_url_kwarg in self.kwargs:
                self._site = get_object_or_404(
                    get_site_model(), slug=self.kwargs.get(self.site_url_kwarg),
                    account=self.account)
            else:
                self._site = get_current_site().db_object
            cache_provider_db(
                self._site.db_name if self._site.db_name else 'default',
                db_host=self._site.db_host, db_port=self._site.db_port)
        return self._site

    def get_actual_domain(self):
        return build_absolute_uri(
            request=self.request, site=self.site, with_scheme=False)

    def get_absolute_uri(self, location=''):
        return build_absolute_uri(location=location,
            request=self.request, site=self.site)
