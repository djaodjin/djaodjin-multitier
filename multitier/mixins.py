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

from django.db import connections
from django.shortcuts import get_object_or_404

from . import get_site_model, settings
from .compat import get_model_class, import_string
from .locals import get_current_site
from .middleware import as_provider_db

class AccountMixin(object):

    account_url_kwarg = settings.ACCOUNT_URL_KWARG

    @property
    def account(self):
        if not hasattr(self, '_account'):
            if settings.ACCOUNT_GET_CURRENT:
                self._account = import_string(settings.ACCOUNT_GET_CURRENT)(
                    self.kwargs.get(self.account_url_kwarg))
            else:
                self._account = get_model_class(settings.ACCOUNT_MODEL,
                    "MULTITIER['ACCOUNT_MODEL']").objects.get(
                    slug=self.kwargs.get(self.account_url_kwarg, None))
        return self._account


class SiteMixin(AccountMixin):
    """
    Returns a ``Site`` from a URL or the default site if none can be found.
    """
    site_url_kwarg = 'site'

    def get_site(self):
        #pylint: disable=access-member-before-definition
        if not hasattr(self, '_site') or self._site is None:
            if self.site_url_kwarg in self.kwargs:
                self._site = get_object_or_404(
                    get_site_model(), slug=self.kwargs.get(self.site_url_kwarg))
            else:
                self._site = get_current_site().project
            db_name = self._site.db_name if self._site.db_name else 'default'
            if not db_name in connections.databases:
                connections.databases[db_name] = as_provider_db(db_name)
        return self._site

    def get_actual_domain(self):
        site = self.get_site()
        if site.domain:
            return site.domain
        return '%s/%s' % (self.request.get_host(), site.slug)

    def get_absolute_uri(self, location=''):
        return '%(scheme)s://%(domain)s/%(path)s' % {
            'scheme': self.request.scheme, 'domain': self.get_actual_domain(),
            'path': location}
