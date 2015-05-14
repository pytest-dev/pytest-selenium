# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ConfigParser import ConfigParser
import os

import pytest
import requests
from selenium import webdriver


name = 'BrowserStack'


def _get_config(option):
    config = ConfigParser()
    config.read('setup.cfg')
    section = 'browserstack'
    if config.has_section(section) and config.has_option(section, option):
        return config.get(section, option)


def _credentials():
    username = os.getenv('BROWSERSTACK_USERNAME', _get_config('username'))
    access_key = os.getenv('BROWSERSTACK_ACCESS_KEY',
                           _get_config('access-key'))
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


def start_driver(item, options, capabilities):
    test_id = '.'.join(_split_class_and_test_names(item.nodeid))
    capabilities.update({
        'name': test_id,
        'browserName': options.browser_name})
    if options.platform is not None:
        capabilities['platform'] = options.platform
    if options.browser_version is not None:
        capabilities['version'] = options.browser_version
    if options.build is not None:
        capabilities['build'] = options.build
    executor = 'http://%s:%s@hub.browserstack.com:80/wd/hub' % _credentials()
    return webdriver.Remote(command_executor=executor,
                            desired_capabilities=capabilities)


def url(session):
    response = requests.get(
        'https://www.browserstack.com/automate/sessions/%s.json' % session,
        auth=_credentials())
    return response.json()['automation_session']['browser_url']


def additional_html(session):
    return []


def update_status(session, passed):
    status = {'status': 'completed' if passed else 'error'}
    requests.put(
        'https://www.browserstack.com/automate/sessions/%s.json' % session,
        headers={'Content-Type': 'application/json'},
        params=status,
        auth=_credentials())
