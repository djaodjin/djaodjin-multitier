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


from django.utils.encoding import iri_to_uri

try:
    from threading import local
except ImportError:
    #pylint: disable=import-error,no-name-in-module
    from django.utils._threading_local import local

_thread_locals = local() #pylint: disable=invalid-name

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
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.db_object.__unicode__()

    def as_absolute_uri(self, path=''):
        if self.db_object.domain:
            host = self.db_object.domain
        else:
            host = self.default_host
        return iri_to_uri('%(scheme)s://%(host)s%(path)s' % {
            'scheme': self.default_scheme, 'host': host, 'path': path})


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


def set_current_site(site, path_prefix,
        default_scheme='http', default_host='localhost'):
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
    return (prev_site, prev_path_prefix)
