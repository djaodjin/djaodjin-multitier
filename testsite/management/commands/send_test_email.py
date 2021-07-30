# Copyright (c) 2021, DjaoDjin inc.
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
This command sends a test e-mail for a site.
"""

import logging

from django.core.management.base import BaseCommand
from django.core.mail import get_connection, send_mail
from multitier.utils import get_site_model


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Send test email"""

    def add_arguments(self, parser):
        parser.add_argument('recipient', metavar='recipient', nargs=1,
            help="recipient of the test e-mail")
        parser.add_argument('sites', metavar='sites', nargs='+',
            help="sites to send test e-mail for")

    def handle(self, *args, **options):
        #pylint:disable=broad-except
        recipient_list = [options['recipient']]
        for site in get_site_model().objects.filter(slug__in=options['sites']):
            send_mail("test", "hello", site.get_from_email(), recipient_list,
              connection=site.get_email_connection())
