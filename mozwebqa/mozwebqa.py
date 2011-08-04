#!/usr/bin/env python
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla WebQA Tests.
#
# The Initial Developer of the Original Code is Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s): Dave Hunt <dhunt@mozilla.com>
#                 David Burns
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import json
import pytest
import py

from selenium import selenium
from selenium import webdriver


def pytest_runtest_setup(item):
    item.api = item.config.option.api
    item.host = item.config.option.host
    item.port = item.config.option.port
    item.browser = item.config.option.browser
    item.environment = item.config.option.environment
    item.browser_name = item.config.option.browser_name
    item.browser_version = item.config.option.browser_version
    item.platform = item.config.option.platform
    TestSetup.base_url = item.config.option.base_url
    TestSetup.timeout = item.config.option.timeout
    item.sauce_labs_username = item.config.option.sauce_labs_username
    item.sauce_labs_api_key = item.config.option.sauce_labs_api_key
    TestSetup.credentials = item.config.option.credentials_file
    
    TestSetup.skip_selenium = True

    _check_usage(item)

    if not 'skip_selenium' in item.keywords:
        TestSetup.skip_selenium = False

        if item.api == 'webdriver':
            _setup_webdriver(item)
        else:
            _setup_selenium(item) 


def pytest_runtest_teardown(item):
    if hasattr(TestSetup, 'selenium') and not TestSetup.skip_selenium:
        if item.api == 'webdriver':
            TestSetup.selenium.quit()
        else:
            if item.config.option.capture_network:
                traffic = TestSetup.selenium.captureNetworkTraffic('json')
                filename = item.keywords.keys()[0]
                f = open('%s.json' % filename, 'w')
                f.write(traffic)
                f.close()
            TestSetup.selenium.stop()


def pytest_funcarg__mozwebqa(request):
    return TestSetup(request)


def pytest_addoption(parser):
    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--api',
                     action = 'store',
                     default = 'webdriver',
                     metavar = 'api',
                     help = "version of selenium api to use. 'rc' uses selenium rc. 'webdriver' uses selenium webdriver (the default).")
    group._addoption('--host',
                     action = 'store',
                     default = 'localhost',
                     metavar = 'str',
                     help = 'host that selenium server is listening on.')
    group._addoption('--port',
                     action = 'store',
                     type = 'int',
                     default = 4444,
                     metavar = 'num',
                     help = 'port that selenium server is listening on.')
    group._addoption('--browser',
                     action = 'store',
                     dest = 'browser',
                     metavar = 'str',
                     help = 'target browser (standalone rc server).')
    group._addoption('--environment',
                     action = 'store',
                     dest = 'environment',
                     metavar = 'str',
                     help = 'target environment (grid rc).')
    group._addoption('--browser-name',
                     action = 'store',
                     dest = 'browser_name',
                     metavar = 'str',
                     help = 'target browser name (webdriver).')
    group._addoption('--browser-ver',
                     action = 'store',
                     dest = 'browser_version',
                     metavar = 'str',
                     help = 'target browser version (webdriver).')
    group._addoption('--platform',
                     action = 'store',
                     metavar = 'str',
                     help = 'target platform (webdriver).')
    group._addoption('--base-url',
                     action = 'store',
                     dest = 'base_url',
                     metavar = 'url',
                     help = 'base url for the application under test.')
    group._addoption('--timeout',
                     action = 'store',
                     type = 'int',
                     default = 60000,
                     metavar = 'num',
                     help = 'timeout for page loads, etc (selenium rc).')
    group._addoption('--capture-network',
                     action = 'store_true',
                     default=False,
                     help = 'capture network traffic to test_method_name.json (selenium rc). (disabled by default).')

    group = parser.getgroup('sauce labs', 'sauce labs')
    group._addoption('--sauce-user',
                     action = 'store',
                     dest = 'sauce_labs_username',
                     metavar = 'str',
                     help = 'sauce labs username.')
    group._addoption('--sauce-key',
                     action = 'store',
                     dest = 'sauce_labs_api_key',
                     metavar = 'str',
                     help = 'sauce labs api key.')

    parser.addoption("--credentials",
                     action="store",
                     dest = 'credentials_file',
                     default="credentials.yaml",
                     metavar = 'path',
                     help="location of yaml file containing user credentials.")

def _check_sauce_usage(item):
    '''
        If this is for SauceLabs usage, we need to check a few details
    '''
    if not item.sauce_labs_username:
        raise pytest.UsageError('--sauce-user must be specified.')
    if not item.sauce_labs_api_key:
        raise pytest.UsageError('--sauce-key must be specified.')
    if item.api is "rc":
        if not item.browser_name:
            raise pytest.UsageError("--browser-name must be specified when using the 'rc' api with sauce labs.")
        if not item.browser_version:
            raise pytest.UsageError("--browser-ver must be specified when using the 'rc' api with sauce labs.")
        if not item.platform:
            raise pytest.UsageError("--platform must be specified when using the 'rc' api with sauce labs.")

def _check_usage(item):
    '''
        Check that the usage parameters are correct. If wrong throws the appropriate error
    '''
    if TestSetup.base_url is None:
        raise pytest.UsageError('--base-url must be specified.')

    item.sauce_labs = item.sauce_labs_username or item.sauce_labs_api_key

    if item.sauce_labs:
        _check_sauce_usage(item)
    
    if item.api == 'webdriver':
        if not item.browser_name:
            raise pytest.UsageError("--browser-name must be specified when using the 'webdriver' api.")
        if not item.browser_version:
            raise pytest.UsageError("--browser-ver must be specified when using the 'webdriver' api.")
        if not item.platform:
            raise pytest.UsageError("--platform must be specified when using the 'webdriver' api.")
    else:
        if not(item.browser or item.environment):
            raise pytest.UsageError("--browser or --environment must be specified when using the 'rc' api.")

    

def _setup_webdriver(item):
    if item.sauce_labs_username:
        capabilities = {
                    'platform': item.platform,
                    'browserName': item.browser_name,
                    'version': item.browser_version,
                    'name': item.keywords.keys()[0],
                    'public': False}
        executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (item.sauce_labs_username, item.sauce_labs_api_key)
        TestSetup.selenium = webdriver.Remote(command_executor = executor,
                                                      desired_capabilities = capabilities)
    else:
        capabilities = getattr(webdriver.DesiredCapabilities, item.browser_name.upper())
        capabilities['version'] = item.browser_version
        capabilities['platform'] = item.platform.upper()
        executor = 'http://%s:%s/wd/hub' % (item.host, item.port)
        try:
            TestSetup.selenium = webdriver.Remote(command_executor = executor,
                                                        desired_capabilities = capabilities)
        except AttributeError:
            valid_browsers = [attr for attr in dir(webdriver.DesiredCapabilities) if not attr.startswith('__')]
            raise AttributeError("Invalid browser name: '%s'. Valid options are: %s" % (item.browser_name, ', '.join(valid_browsers)))

def _setup_selenium(item):
    if item.sauce_labs_username:
        TestSetup.selenium = selenium('ondemand.saucelabs.com', '80',
                                      json.dumps({
                                      'username': item.sauce_labs_username,
                                      'access-key':  item.sauce_labs_api_key,
                                      'os': item.platform,
                                      'browser': item.browser_name,
                                      'browser-version': item.browser_version,
                                      'name': item.keywords.keys()[0],
                                      'public': False}),
                                      TestSetup.base_url)
    else:
        browser = item.environment or item.browser
        TestSetup.selenium = selenium(item.host, str(item.port), browser, TestSetup.base_url)

    if item.config.option.capture_network:
        TestSetup.selenium.start("captureNetworkTraffic=true")
    else:
        TestSetup.selenium.start()

    TestSetup.selenium.set_timeout(TestSetup.timeout)


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
