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

import re

from django import VERSION as DJANGO_VERSION
from django.utils.translation.trans_real import DjangoTranslation

from .compat import RegexURLResolver
from .thread_locals import get_current_site


class SiteCode(DjangoTranslation):

    def __init__(self, *args, **kw):
        # Django 1.7:
        #    def __init__(self, *args, **kw):
        #        gettext_module.GNUTranslations.__init__(self, *args, **kw)
        # Django 1.8:
        #    def __init__(self, language):
        #        gettext_module.GNUTranslations.__init__(self)
        #        self.__language = language
        # XXX Django 1.8 prototype is very strange since the call
        #     from gettext.py will be:
        #         with open(mofile, 'rb') as fp:
        #             t = _translations.setdefault(key, class_(fp))
        if DJANGO_VERSION[0] == 1 and DJANGO_VERSION[1] < 8:
            DjangoTranslation.__init__(self, *args, **kw)
        else:
            DjangoTranslation.__init__(self, 'en-us')
        self._catalog = {}
        self.set_output_charset('utf-8')
        self.__language = 'en-us'

    def set_language(self, language):
        self.__language = language

    def language(self):
        return self.__language

    def to_language(self):
        current_site = get_current_site()
        if current_site and current_site.path_prefix:
            # current_site will be None when 'manage.py show_urls' is invoked.
            return current_site.path_prefix
        return 'en-us'


class SiteRegexURLResolver(RegexURLResolver):
    """
    A URL resolver that always matches the active organization code
    as URL prefix.
    """
    def __init__(self, urlconf_name,
                 default_kwargs=None, app_name=None, namespace=None):
        super(SiteRegexURLResolver, self).__init__(
            None, urlconf_name, default_kwargs, app_name, namespace)

    @property
    def regex(self):
        current_site = get_current_site()
        if current_site and current_site.path_prefix:
            # site will be None when 'manage.py show_urls' is invoked.
            return re.compile('^%s/' % current_site.path_prefix, re.UNICODE)
        return re.compile('^', re.UNICODE)


def site_patterns(*args):
    """
    Adds the live organization prefix to every URL pattern within this
    function. This may only be used in the root URLconf, not in an included
    URLconf.
    """
    pattern_list = args
    return [SiteRegexURLResolver(pattern_list)]
