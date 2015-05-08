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


try:
    from threading import local
except ImportError:
    #pylint: disable=import-error,no-name-in-module
    from django.utils._threading_local import local

_thread_locals = local() #pylint: disable=invalid-name

class CurrentSite(object):

    def __init__(self, project, path_prefix):
        self.project = project
        self.path_prefix = path_prefix

    def __getattr__(self, name):
        return getattr(self.project, name)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.project.__unicode__()


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


def set_current_site(project, path_prefix):
    _thread_locals.site = CurrentSite(project, path_prefix)
