# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ConfigParser import ConfigParser
import os

import requests
from selenium import webdriver


class BrowserStack(object):

    name = 'BrowserStack'

    def __init__(self):
        username = None
        access_key = None

        config = ConfigParser()
        config.read('setup.cfg')

        section = 'browserstack'
        if config.has_section(section):
            if config.has_option(section, 'username'):
                username = config.get(section, 'username')
            if config.has_option(section, 'access-key'):
                access_key = config.get(section, 'access-key')

        self.username = os.getenv('BROWSERSTACK_USERNAME', username)
        self.access_key = os.getenv('BROWSERSTACK_ACCESS_KEY', access_key)

        if self.username is None:
            raise ValueError('BrowserStack username must be set!')
        if self.access_key is None:
            raise ValueError('BrowserStack access key must be set!')

    def driver(self, test_id, capabilities, options):
        capabilities.update({
            'name': test_id,
            'browserName': options.browser_name,
            'platform': options.platform})
        if options.browser_version is not None:
            capabilities['version'] = options.browser_version
        if options.build is not None:
            capabilities['build'] = options.build
        executor = 'http://%s:%s@hub.browserstack.com:80/wd/hub' % (
            self.username, self.access_key)
        return webdriver.Remote(
            command_executor=executor,
            desired_capabilities=capabilities)

    def url(self, session):
        r = requests.get('https://www.browserstack.com/automate/sessions/%s.json' % session,
                         auth=(self.username, self.access_key))
        return r.json()['automation_session']['browser_url']

    def additional_html(self, session):
        return []

    def update_status(self, session, passed):
        status = {'status': 'completed' if passed else 'error'}
        requests.put('https://www.browserstack.com/automate/sessions/%s.json' % session,
                     headers={'Content-Type': 'application/json'},
                     params=status,
                     auth=(self.username, self.access_key))
