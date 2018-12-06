"""
sentry_groveio.models
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by Matt Robenolt, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import json
import urllib
import urllib2
import logging

from django import forms

from sentry.plugins.bases import notify

logger = logging.getLogger('sentry.plugins.groveio')


class GroveIoOptionsForm(notify.NotificationConfigurationForm):
    token = forms.CharField(help_text="Your Grove.io channel token.")
    service_name = forms.CharField(help_text="Name of the service (displayed in the message)", initial='Sentry')
    url = forms.CharField(help_text="(Optional) Service URL for the web client", required=False)
    icon_url = forms.CharField(help_text="(Optional) Icon for the service", required=False)


class GroveIoPlugin(notify.NotificationPlugin):
    author = 'Matt Robenolt'
    author_url = 'https://github.com/mattrobenolt'
    description = 'Post new exceptions to a Grove.io room.'
    resource_links = (
        ('Bug Tracker', 'http://github.com/mattrobenolt/sentry-groveio/issues'),
        ('Source', 'http://github.com/mattrobenolt/sentry-groveio'),
    )

    title = 'Grove.io'
    slug = 'grove-io'
    conf_key = 'groveio'
    description = 'Send errors to Grove.io'
    version = '0.2.0'
    project_conf_form = GroveIoOptionsForm

    def is_configured(self, project):
        return all((self.get_option(k, project) for k in ('token', 'service_name')))

    def notify_users(self, group, event, fail_silently=False, **kwargs):
        token = self.get_option('token', event.project)
        service = self.get_option('service_name', event.project)
        message = '[%s] %s: %s' % (event.server_name, event.get_level_display().upper(), event.error().encode('utf-8').split('\n')[0])
        self.send_payload(token, service, event, group, message)

    def send_payload(self, token, service, event, group, message):
        url = "https://grove.io/api/notice/%s/" % token
        values = {
            'service': service,
            'message': message,
            'url': group.get_absolute_url(),
            'icon_url': self.get_option('icon_url', event.project)
        }

        # Can we just use `requests' please?
        data = urllib.urlencode(values)
        request = urllib2.Request(url, data)
        try:
            urllib2.urlopen(request)
        except urllib2.URLError:
            logger.error('Could not connect to Grove.io')
        except urllib2.HTTPError, e:
            try:
                error = json.loads(e.read())
            except json.decoder.JSONDecodeError:
                logger.error('Something bad happened with Grove. :(')
            if 'error' in error:
                logger.error(error['error'])
            else:
                logger.error('Something bad happened with Grove. :(')
