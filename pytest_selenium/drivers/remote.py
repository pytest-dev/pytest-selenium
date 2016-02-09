# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest
from selenium.webdriver import Remote


def pytest_addoption(parser):
    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--host',
                     default=os.environ.get('SELENIUM_HOST', 'localhost'),
                     metavar='str',
                     help='host that selenium server is listening on. '
                          '(default: %default)')
    group._addoption('--port',
                     type='int',
                     default=os.environ.get('SELENIUM_PORT', 4444),
                     metavar='num',
                     help='port that selenium server is listening on. '
                          '(default: %default)')


@pytest.fixture
def remote_driver(request, capabilities, firefox_profile):
    """Return a WebDriver using a Selenium server or Selenium Grid instance"""
    if 'browserName' not in capabilities:
        # remote instances must at least specify a browserName capability
        raise pytest.UsageError('The \'browserName\' capability must be '
                                'specified when using the remote driver.')
    capabilities.setdefault('version', '')  # default to any version
    capabilities.setdefault('platform', 'ANY')  # default to any platform
    executor = 'http://{host}:{port}/wd/hub'.format(
        host=request.config.getoption('host'),
        port=request.config.getoption('port'))
    return Remote(
        command_executor=executor,
        desired_capabilities=capabilities,
        browser_profile=firefox_profile)
