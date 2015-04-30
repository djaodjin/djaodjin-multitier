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

import logging

from django.conf import settings
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.utils._os import safe_join

from .locals import get_current_site

LOGGER = logging.getLogger(__name__)

class Loader(FilesystemLoader):

    def get_template_sources(self, template_name, template_dirs=None):
        try:
            if not template_dirs:
                template_dirs = settings.TEMPLATE_DIRS
            themes = []
            current_site = get_current_site()
            if current_site:
                themes = current_site.get_templates()
            for theme in themes:
                for template_dir in template_dirs:
                    try:
                        template_path = safe_join(
                            template_dir, theme, template_name)
                        yield template_path
                    except UnicodeDecodeError:
                        # The template dir name was a bytestring that wasn't
                        # valid UTF-8.
                        raise
                    except ValueError:
                        # The joined path was located outside
                        # of this particular template_dir (it might be
                        # inside another one, so this isn't fatal).
                        pass

        except AttributeError, attr_err:
            # Something bad appended. We don't even have a request.
            # The middleware might be misconfigured.
            LOGGER.warning(
                "%s, your middleware might be misconfigured.", attr_err)
