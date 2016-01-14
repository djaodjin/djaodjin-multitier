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

from collections import OrderedDict
import os

from django.conf import settings as django_settings
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles import utils

from .locals import get_current_site
from .settings import STATICFILES_DIRS

#pylint:disable=no-member
class MultitierFileSystemFinder(FileSystemFinder):
    """
    A static files finder that uses ``get_current_site()`` to locate files.
    """

    def get_locations(self):
        locations = []
        storages = OrderedDict()
        postfix = django_settings.STATIC_URL
        if postfix.startswith('/'):
            postfix = postfix[1:]
        roots = []
        site = get_current_site()
        if site is not None:
            # ``site`` could be ``None`` when this code is used through
            # a manage.py command (ex: collectstatic).
            roots += [os.path.join(static_dir,
                theme, postfix) for static_dir in STATICFILES_DIRS
                    for theme in get_current_site().get_templates()]
        for root in roots:
            prefix = ''
            if not (prefix, root) in locations:
                locations.append((prefix, root))
                filesystem_storage = FileSystemStorage(location=root)
                filesystem_storage.prefix = prefix
                storages[root] = filesystem_storage
        locations = locations + self.locations
        storages.update(self.storages)
        return locations, storages

    def find(self, path, all=False):
        """
        Looks for files in the extra locations
        as defined in ``STATICFILES_DIRS`` and multitier locations.
        """
        matches = []
        locations, _ = self.get_locations()
        for prefix, root in locations:
            matched_path = self.find_location(root, path, prefix)
            if matched_path:
                if not all:
                    return matched_path
                matches.append(matched_path)
        return matches

    def list(self, ignore_patterns):
        """
        List all files in all locations.
        """
        locations, storages = self.get_locations()
        for prefix, root in locations:
            storage = storages[root]
            for path in utils.get_files(storage, ignore_patterns):
                yield path, storage
