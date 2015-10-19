# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests
from selenium import webdriver

from .base import CloudProvider


class Provider(CloudProvider):

    _session_url = 'https://www.browserstack.com/automate/sessions/{id}.json'

    @property
    def name(self):
        return 'BrowserStack'

    def _username(self, config):
        username = config.getini('browserstack_username')
        if not username:
            raise pytest.UsageError('BrowserStack username must be set')
        return username

    def _access_key(self, config):
        access_key = config.getini('browserstack_access_key')
        if not access_key:
            raise pytest.UsageError('BrowserStack access key must be set')
        return access_key

    def start_driver(self, item, capabilities):
        test_id = '.'.join(self.split_class_and_test_names(item.nodeid))
        capabilities['name'] = test_id
        executor = 'http://{0}:{1}@hub.browserstack.com:80/wd/hub'.format(
            self._username(item.config), self._access_key(item.config))
        return webdriver.Remote(command_executor=executor,
                                desired_capabilities=capabilities)

    def url(self, config, session):
        response = requests.get(self._session_url.format(id=session),
                                auth=(self._username(config),
                                      self._access_key(config)))
        return response.json()['automation_session']['browser_url']

    def additional_html(self, session):
        return ''

    def update_status(self, config, session, passed):
        status = {'status': 'completed' if passed else 'error'}
        requests.put(self._session_url.format(id=session),
                     headers={'Content-Type': 'application/json'},
                     params=status,
                     auth=(self._username(config), self._access_key(config)))
