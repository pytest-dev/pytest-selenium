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
import urllib2

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import selenium
from selenium import webdriver
import yaml


def pytest_configure(config):
    if config.option.base_url:
        assert _get_status_code(config.option.base_url) == 200

def pytest_runtest_setup(item):
    item.api = item.config.option.api
    item.host = item.config.option.host
    item.port = item.config.option.port
    item.driver = item.config.option.driver
    item.chrome_path = item.config.option.chrome_path
    item.firefox_path = item.config.option.firefox_path
    item.browser = item.config.option.browser
    item.environment = item.config.option.environment
    item.browser_name = item.config.option.browser_name
    item.browser_version = item.config.option.browser_version
    item.platform = item.config.option.platform
    TestSetup.base_url = item.config.option.base_url
    TestSetup.timeout = item.config.option.timeout
    TestSetup.default_implicit_wait = 10
    item.sauce_labs_credentials_file = item.config.option.sauce_labs_credentials_file

    if item.sauce_labs_credentials_file:
        item.sauce_labs_credentials = _credentials(item.config.option.sauce_labs_credentials_file)

    item.credentials_file = item.config.option.credentials_file

    if item.credentials_file:
        TestSetup.credentials = _credentials(item.credentials_file)

    if not 'skip_selenium' in item.keywords:
        _check_selenium_usage(item)
        _start_selenium(item)
    else:
        TestSetup.selenium = None


def pytest_runtest_teardown(item):
    if not 'skip_selenium' in item.keywords:
        _stop_selenium(item)


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
    group._addoption('--driver',
                     action = 'store',
                     dest = 'driver',
                     default = 'Remote',
                     metavar = 'str',
                     help = 'webdriver implementation.')
    group._addoption('--chromepath',
                     action = 'store',
                     dest = 'chrome_path',
                     metavar = 'path',
                     help = 'path to the google chrome driver executable.')
    group._addoption('--firefoxpath',
                     action = 'store',
                     dest = 'firefox_path',
                     metavar = 'path',
                     help = 'path to the target firefox binary.')
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
    group._addoption('--browsername',
                     action = 'store',
                     dest = 'browser_name',
                     metavar = 'str',
                     help = 'target browser name (webdriver).')
    group._addoption('--browserver',
                     action = 'store',
                     dest = 'browser_version',
                     metavar = 'str',
                     help = 'target browser version (webdriver).')
    group._addoption('--platform',
                     action = 'store',
                     metavar = 'str',
                     help = 'target platform (webdriver).')
    group._addoption('--baseurl',
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
    group._addoption('--capturenetwork',
                     action = 'store_true',
                     dest = 'capture_network',
                     default=False,
                     help = 'capture network traffic to test_method_name.json (selenium rc). (disabled by default).')

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--credentials",
                     action="store",
                     dest = 'credentials_file',
                     metavar = 'path',
                     help="location of yaml file containing user credentials.")
    group._addoption('--saucelabs',
                     action = 'store',
                     dest = 'sauce_labs_credentials_file',
                     metavar = 'path',
                     help = 'credendials file containing sauce labs username and api key.')

def _get_status_code(url):
    try:
        connection = urllib2.urlopen(url)
        status_code = connection.getcode()
        connection.close()
        return status_code
    except urllib2.URLError, e:
        print 'Unable to connect to: %s' % url
        raise


def _credentials(credentials_file):
    stream = file(credentials_file, 'r')
    credentials = yaml.load(stream)
    return credentials


def _check_sauce_usage(item):
    '''
        If this is for Sauce Labs usage, we need to check a few details
    '''
    if not item.sauce_labs_credentials['username']:
        raise pytest.UsageError('username must be specified in the sauce labs credentials file.')

    if not item.sauce_labs_credentials['api-key']:
        raise pytest.UsageError('api-key must be specified in the sauce labs credentials file.')

    if item.api == "rc":
        if not item.browser_name:
            raise pytest.UsageError("--browsername must be specified when using the 'rc' api with sauce labs.")

        if not item.browser_version:
            raise pytest.UsageError("--browserver must be specified when using the 'rc' api with sauce labs.")

        if not item.platform:
            raise pytest.UsageError("--platform must be specified when using the 'rc' api with sauce labs.")


def _check_selenium_usage(item):
    '''
        Check that the usage parameters are correct. If wrong throws the appropriate error
    '''
    if TestSetup.base_url is None:
        raise pytest.UsageError('--baseurl must be specified.')

    if item.sauce_labs_credentials_file:
        _check_sauce_usage(item)

    if item.api == 'webdriver':
        if item.driver.upper() == 'REMOTE':
            if not item.browser_name:
                raise pytest.UsageError("--browsername must be specified when using the 'webdriver' api.")

            if not item.browser_version:
                raise pytest.UsageError("--browserver must be specified when using the 'webdriver' api.")

            if not item.platform:
                raise pytest.UsageError("--platform must be specified when using the 'webdriver' api.")
    else:
        if not item.sauce_labs_credentials_file and not(item.browser or item.environment):
            raise pytest.UsageError("--browser or --environment must be specified when using the 'rc' api.")


def _start_selenium(item):
    if item.api == 'webdriver':
        _start_webdriver_client(item)
    else:
        _start_rc_client(item) 


def _start_webdriver_client(item):
    if item.sauce_labs_credentials_file:
        capabilities = {
                    'platform': item.platform,
                    'browserName': item.browser_name,
                    'version': item.browser_version,
                    'name': item.keywords.keys()[0],
                    'public': False}
        executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (item.sauce_labs_credentials['username'], item.sauce_labs_credentials['api-key'])
        TestSetup.selenium = webdriver.Remote(command_executor = executor,
                                                      desired_capabilities = capabilities)
    else:
        if item.driver.upper() == 'REMOTE':
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

        elif item.driver.upper() == 'CHROME':
            if hasattr(item, 'chrome_path'):
                TestSetup.selenium = webdriver.Chrome(executable_path=item.chrome_path)
            else:
                TestSetup.selenium = webdriver.Chrome()

        elif item.driver.upper() == 'FIREFOX':
            if hasattr(item, 'firefox_path'):
                TestSetup.selenium = webdriver.Firefox(firefox_binary=FirefoxBinary(item.firefox_path))
            else:
                TestSetup.selenium = webdriver.Firefox()

        elif item.driver.upper() == 'IE':
            TestSetup.selenium = webdriver.Ie()
        else:
            getattr(webdriver, item.driver)()

    TestSetup.selenium.implicitly_wait(TestSetup.default_implicit_wait)


def _start_rc_client(item):
    if item.sauce_labs_credentials_file:
        TestSetup.selenium = selenium('ondemand.saucelabs.com', '80',
                                      json.dumps({
                                      'username': item.sauce_labs_credentials['username'],
                                      'access-key': item.sauce_labs_credentials['api-key'],
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


def _stop_selenium(item):
    if item.api == 'webdriver':
        try:
            TestSetup.selenium.quit()
        except:
            pass
    else:
        if item.config.option.capture_network:
            traffic = TestSetup.selenium.captureNetworkTraffic('json')
            filename = item.keywords.keys()[0]
            f = open('%s.json' % filename, 'w')
            f.write(traffic)
            f.close()
        try:
            TestSetup.selenium.stop()
        except:
            pass


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
