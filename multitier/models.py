# Copyright (c) 2017, Djaodjin Inc.
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

"""
Models for the multi-tier application.
"""

import string

from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils._os import safe_join
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from . import settings
from .utils import get_site_model


SUBDOMAIN_RE = r'^[-a-zA-Z0-9_]+\Z'
SUBDOMAIN_SLUG = RegexValidator(
    SUBDOMAIN_RE,
    _("Enter a valid subdomain consisting of letters, digits or hyphens."),
    'invalid'
)


def domain_name_validator(value):
    """
    Validates that the given value contains no whitespaces to prevent common
    typos.
    """
    if not value:
        return
    checks = ((s in value) for s in string.whitespace)
    if any(checks):
        raise ValidationError(
            _("The domain name cannot contain any spaces or tabs."),
            code='invalid',
        )

@python_2_unicode_compatible
class Site(models.Model):

    # Since most DNS provider limit subdomain length to 25 characters,
    # we do here too.
    slug = models.SlugField(unique=True, max_length=25,
        validators=[SUBDOMAIN_SLUG],
        help_text="unique identifier for the site (also serves as subdomain)")
    domain = models.CharField(null=True, blank=True, max_length=100,
        help_text='fully qualified domain name at which the site is available',
        validators=[domain_name_validator, RegexValidator(
            URLValidator.host_re,
            "Enter a valid 'domain', ex: example.com", 'invalid')])
    account = models.ForeignKey(
        settings.ACCOUNT_MODEL, null=True, on_delete=models.CASCADE,
        related_name='sites')

    db_name = models.SlugField(null=True,
        help_text='name of database to connect to for the site')
    db_host = models.CharField(max_length=255, null=True,
        help_text='host to connect to to access the database')
    db_port = models.IntegerField(null=True,
        help_text='port to connect to to access the database')

    base = models.ForeignKey('multitier.Site',
        null=True, on_delete=models.CASCADE,
        help_text='The site is a derivative of this parent.')
    is_active = models.BooleanField(default=False)
    is_path_prefix = models.BooleanField(default=False,
        help_text="use slug as a prefix for URL paths instead of domain field.")
    tag = models.CharField(null=True, max_length=255)
    cert_location = models.CharField(null=True, max_length=1024)

    class Meta:
        swappable = 'MULTITIER_SITE_MODEL'

    def __str__(self): #pylint: disable=super-on-old-class
        return self.slug

    def as_base(self):
        """
        Returns either the base site or ``self`` if no base exists.
        """
        if self.base_id:
            return self.base
        return self

    def as_subdomain(self):
        return self.slug

    @property
    def printable_name(self):
        return self.slug

    def get_templates(self):
        """
        Returns a list of candidate themes.
        """
        return [self.slug]

    def get_template_dirs(self):
        """
        Returns a list of candidate search paths for templates.
        """
        return [safe_join(theme_dir, theme, 'templates')
                for theme_dir in settings.THEMES_DIRS
                    for theme in self.get_templates()]

    def add_tags(self, tags):
        tags = [''] + tags # make a clone since we are going to be destructive.
                           # also add the extra coma prefix needed later on.
        for tag in self.tag.split(','):
            if tag in tags:
                tags = [rec for rec in tags if rec != tag]
        self.tag += ','.join(tags)

    def remove_tags(self, tags):
        self.tag = ','.join([
            tag for tag in self.tag.split(',') if tag not in tags])


def get_site_or_none(subdomain):
    """
    Returns a ``Site`` instance based on its subdomain while prefering
    ``Site`` with an explicit domain.
    If no Site could be found, then returns ``None``.
    """
    return get_site_model().objects.filter(
        slug=subdomain).order_by('domain', '-pk').first()
