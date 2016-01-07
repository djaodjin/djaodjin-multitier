# Copyright (c) 2015, DjaoDjin inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Convenience module for access of multitier application settings, which enforces
default settings when the main settings module does not contain
the appropriate settings.
"""
import os

from django.conf import settings

_SETTINGS = {
    'ACCOUNT_MODEL': settings.AUTH_USER_MODEL,
    'ACCOUNT_GET_CURRENT': None,
    'ACCOUNT_URL_KWARG': None,
    'DEFAULT_DOMAIN': 'localhost:8000',
    'ROUTER_APPS': ('auth', 'sessions', 'contenttypes'),
    'ROUTER_TABLES': [],
    'DEBUG_SQLITE3_PATHS': [],
    'THEMES_DIR': os.path.join(settings.BASE_DIR, 'themes')
}
_SETTINGS.update(getattr(settings, 'MULTITIER', {}))

SLUG_RE = r'[a-zA-Z0-9\-]+'

ACCOUNT_MODEL = _SETTINGS.get('ACCOUNT_MODEL')
ACCOUNT_GET_CURRENT = _SETTINGS.get('ACCOUNT_GET_CURRENT')
ACCOUNT_URL_KWARG = _SETTINGS.get('ACCOUNT_URL_KWARG')
DEFAULT_DOMAIN = _SETTINGS.get('DEFAULT_DOMAIN')
ROUTER_APPS = _SETTINGS.get('ROUTER_APPS')
ROUTER_TABLES = _SETTINGS.get('ROUTER_TABLES')
DEBUG_SQLITE3_PATHS = _SETTINGS.get('DEBUG_SQLITE3_PATHS')
THEMES_DIR = _SETTINGS.get('THEMES_DIR')
