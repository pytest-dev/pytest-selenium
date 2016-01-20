# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from selenium.webdriver import Remote


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
