# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests
from selenium import webdriver


name = 'BrowserStack'


def _credentials(config):
    username = config.getini('browserstack_username')
    access_key = config.getini('browserstack_access_key')
    if not username:
        raise pytest.UsageError('BrowserStack username must be set')
    if not access_key:
        raise pytest.UsageError('BrowserStack access key must be set')
    return username, access_key


def _split_class_and_test_names(nodeid):
    # TODO remove duplication of shared code
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def start_driver(item, capabilities):
    test_id = '.'.join(_split_class_and_test_names(item.nodeid))
    capabilities['name'] = test_id
    executor = 'http://%s:%s@hub.browserstack.com:80/wd/hub' % \
        _credentials(item.config)
    return webdriver.Remote(command_executor=executor,
                            desired_capabilities=capabilities)


def url(config, session):
    response = requests.get(
        'https://www.browserstack.com/automate/sessions/%s.json' % session,
        auth=_credentials(config))
    return response.json()['automation_session']['browser_url']


def additional_html(session):
    return []


def update_status(config, session, passed):
    status = {'status': 'completed' if passed else 'error'}
    requests.put(
        'https://www.browserstack.com/automate/sessions/%s.json' % session,
        headers={'Content-Type': 'application/json'},
        params=status,
        auth=_credentials(config))
