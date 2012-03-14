#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import pytest
import py
import re
import ConfigParser

import requests
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import selenium
from selenium import webdriver
import yaml


__version__ = '0.9'

def pytest_configure(config):
    if not hasattr(config, 'slaveinput'):

        config.addinivalue_line(
            'markers', 'nondestructive: mark the test as nondestructive. ' \
            'Tests are assumed to be destructive unless this marker is ' \
            'present. This reduces the risk of running destructive tests ' \
            'accidentally.')

        if config.option.base_url:
            r = requests.get(config.option.base_url)
            assert r.status_code == 200, 'Base URL did not return status code 200. (URL: %s, Response: %s)' % (config.option.base_url, r.status_code)

        if config.option.webqa_report_path:
            from html_report import HTMLReport
            config._html = HTMLReport(config)
            config.pluginmanager.register(config._html)

        if not config.option.run_destructive:
            if config.option.markexpr:
                config.option.markexpr = 'nondestructive and (%s)' % config.option.markexpr
            else: 
                config.option.markexpr = 'nondestructive'


def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


def pytest_runtest_setup(item):
    item.debug = _create_debug()
    TestSetup.base_url = item.config.option.base_url
    TestSetup.default_implicit_wait = 10

    # consider this environment sensitive if the base url or any redirection
    # history matches the regular expression
    sensitive = False
    if TestSetup.base_url:
        r = requests.get(TestSetup.base_url)
        urls = [h.url for h in r.history] + [r.url]
        matches = [re.search(item.config.option.sensitive_url, u) for u in urls]
        sensitive = any(matches)

    destructive = 'nondestructive' not in item.keywords

    if (sensitive and destructive):
        first_match = matches[next(i for i, match in enumerate(matches) if match)]

        # skip the test with an appropriate message
        py.test.skip('This test is destructive and the target URL is ' \
                     'considered a sensitive environment. If this test is ' \
                     'not destructive, add the \'nondestructive\' marker to ' \
                     'it. Sensitive URL: %s' % first_match.string)

    if item.config.option.api.upper() == 'RC':
        TestSetup.timeout = item.config.option.timeout * 1000
    else:
        TestSetup.timeout = item.config.option.timeout

    if item.config.option.sauce_labs_credentials_file:
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
    if hasattr(TestSetup, 'selenium') and TestSetup.selenium and not 'skip_selenium' in item.keywords:
        _stop_selenium(item)


def pytest_runtest_makereport(__multicall__, item, call):
    report = __multicall__.execute()
    if report.when == 'call':
        report.session_id = getattr(item, 'session_id', None)
        if hasattr(TestSetup, 'selenium') and TestSetup.selenium and not 'skip_selenium' in item.keywords:
            if report.skipped and 'xfail' in report.keywords or report.failed and 'xfail' not in report.keywords:
                _capture_url(item)
                _capture_screenshot(item)
                _capture_html(item)
                _capture_log(item)
                report.sections.append(('pytest-mozwebqa', _debug_summary(item.debug)))
            _capture_network_traffic(item)
            report.debug = item.debug
    return report


def pytest_funcarg__mozwebqa(request):
    return TestSetup(request)


def pytest_addoption(parser):
    config = ConfigParser.ConfigParser(defaults={
        'baseurl': '',
        'api': 'webdriver'
    })
    config.read('mozwebqa.cfg')

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--baseurl',
                     action='store',
                     dest='base_url',
                     default=config.get('DEFAULT', 'baseurl'),
                     metavar='url',
                     help='base url for the application under test.')
    group._addoption('--api',
                     action='store',
                     default=config.get('DEFAULT', 'api'),
                     metavar='api',
                     help="version of selenium api to use. 'rc' uses selenium rc. 'webdriver' uses selenium webdriver. (default: %default)")
    group._addoption('--host',
                     action='store',
                     default='localhost',
                     metavar='str',
                     help='host that selenium server is listening on. (default: %default)')
    group._addoption('--port',
                     action='store',
                     type='int',
                     default=4444,
                     metavar='num',
                     help='port that selenium server is listening on. (default: %default)')
    group._addoption('--driver',
                     action='store',
                     dest='driver',
                     default='Remote',
                     metavar='str',
                     help='webdriver implementation. (default: %default)')
    group._addoption('--capabilities',
                     action='store',
                     dest='capabilities',
                     metavar='str',
                     help='json string of additional capabilties to set (webdriver).')
    group._addoption('--chromepath',
                     action='store',
                     dest='chrome_path',
                     metavar='path',
                     help='path to the google chrome driver executable.')
    group._addoption('--firefoxpath',
                     action='store',
                     dest='firefox_path',
                     metavar='path',
                     help='path to the target firefox binary.')
    group._addoption('--firefoxpref',
                     action='store',
                     dest='firefox_preferences',
                     metavar='str',
                     help='json string of firefox preferences to set (webdriver).')
    group._addoption('--chromeopts',
                     action='store',
                     dest='chrome_options',
                     metavar='str',
                     help='json string of google chrome options to set (webdriver).')
    group._addoption('--browser',
                     action='store',
                     dest='browser',
                     metavar='str',
                     help='target browser (standalone rc server).')
    group._addoption('--environment',
                     action='store',
                     dest='environment',
                     metavar='str',
                     help='target environment (grid rc).')
    group._addoption('--browsername',
                     action='store',
                     dest='browser_name',
                     metavar='str',
                     help='target browser name (webdriver).')
    group._addoption('--browserver',
                     action='store',
                     dest='browser_version',
                     metavar='str',
                     help='target browser version (webdriver).')
    group._addoption('--platform',
                     action='store',
                     metavar='str',
                     help='target platform (webdriver).')
    group._addoption('--timeout',
                     action='store',
                     type='int',
                     default=60,
                     metavar='num',
                     help='timeout (in seconds) for page loads, etc. (default: %default)')
    group._addoption('--capturenetwork',
                     action='store_true',
                     dest='capture_network',
                     default=False,
                     help='capture network traffic to test_method_name.json (selenium rc). (default: %default)')
    group._addoption('--build',
                     action='store',
                     dest='build',
                     metavar='str',
                     help='build identifier (for continuous integration).')

    group = parser.getgroup('safety', 'safety')
    group._addoption('--sensitiveurl',
                     action='store',
                     dest='sensitive_url',
                     default='mozilla\.(com|org)',
                     metavar='str',
                     help='regular expression for identifying sensitive urls. (default: %default)')
    group._addoption('--destructive',
                     action='store_true',
                     dest='run_destructive',
                     default=False,
                     help='include destructive tests (tests not explicitly marked as \'nondestructive\'). (default: %default)')

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--credentials",
                     action="store",
                     dest='credentials_file',
                     metavar='path',
                     help="location of yaml file containing user credentials.")
    group._addoption('--saucelabs',
                     action='store',
                     dest='sauce_labs_credentials_file',
                     metavar='path',
                     help='credendials file containing sauce labs username and api key.')

    group = parser.getgroup("terminal reporting")
    group.addoption('--webqareport',
                    action='store',
                    dest='webqa_report_path',
                    metavar='path',
                    default='results/index.html',
                    help='create mozilla webqa custom report file at given path. (default: %default)')


def split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def _create_debug():
    return {
        'urls': [],
        'screenshots': [],
        'html': [],
        'logs': [],
        'network_traffic': []}


def _debug_summary(debug):
    summary = []
    if debug['urls']:
        summary.append('Failing URL: %s' % debug['urls'][-1])
    return '\n'.join(summary)


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

    if item.config.option.api == "rc":
        if not item.config.option.browser_name:
            raise pytest.UsageError("--browsername must be specified when using the 'rc' api with sauce labs.")

        if not item.config.option.browser_name:
            raise pytest.UsageError("--browserver must be specified when using the 'rc' api with sauce labs.")

        if not item.config.option.browser_name:
            raise pytest.UsageError("--platform must be specified when using the 'rc' api with sauce labs.")


def _check_selenium_usage(item):
    '''
        Check that the usage parameters are correct. If wrong throws the appropriate error
    '''
    if not TestSetup.base_url:
        raise pytest.UsageError('--baseurl must be specified.')

    if item.config.option.sauce_labs_credentials_file:
        _check_sauce_usage(item)

    if item.config.option.api == 'webdriver':
        if item.config.option.driver.upper() == 'REMOTE':
            if not item.config.option.browser_name:
                raise pytest.UsageError("--browsername must be specified when using the 'webdriver' api.")

            if not item.config.option.browser_name:
                raise pytest.UsageError("--browserver must be specified when using the 'webdriver' api.")

            if not item.config.option.browser_name:
                raise pytest.UsageError("--platform must be specified when using the 'webdriver' api.")
    else:
        if not item.config.option.sauce_labs_credentials_file and not(item.config.option.browser or item.config.option.environment):
            raise pytest.UsageError("--browser or --environment must be specified when using the 'rc' api.")


def _get_common_sauce_settings(item):
    config = ConfigParser.ConfigParser(defaults={'tags': ''})
    config.read('mozwebqa.cfg')
    tags = config.get('DEFAULT', 'tags').split(',')
    tags.extend([mark for mark in item.keywords.keys() if not mark.startswith('test')])
    return {'build': item.config.option.build or None,
            'name': '.'.join(split_class_and_test_names(item.nodeid)),
            'tags': tags,
            'public': 'private' not in item.keywords,
            'restricted-public-info': 'public' not in item.keywords}


def _create_firefox_profile(preferences):
    if preferences:
        profile = webdriver.FirefoxProfile()
        for key, value in json.loads(preferences).items():
            if isinstance(value, unicode):
                value = str(value)
            profile.set_preference(key, value)
        profile.update_preferences()
        return profile
    else:
        return None


def _create_chrome_options(preferences):
    options = webdriver.ChromeOptions()
    options_from_json = json.loads(preferences)

    if 'arguments' in options_from_json:
        for args_ in options_from_json['arguments']:
            options.add_argument(args_)

    if 'extensions' in options_from_json:
        for ext_ in options_from_json['extensions']:
            options.add_extension(ext_)

    if 'binary_location' in options_from_json:
        options.binary_location = options_from_json['binary_location']

    return options


def _start_selenium(item):
    if item.config.option.api == 'webdriver':
        _start_webdriver_client(item)
    else:
        _start_rc_client(item)
    _capture_session_id(item)


def _start_webdriver_client(item):
    if item.config.option.sauce_labs_credentials_file:
        capabilities = _get_common_sauce_settings(item)
        capabilities.update({'platform': item.config.option.platform,
                         'browserName': item.config.option.browser_name,
                         'version': item.config.option.browser_version})
        if item.config.option.capabilities:
            capabilities.update(json.loads(item.config.option.capabilities))
        executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (item.sauce_labs_credentials['username'], item.sauce_labs_credentials['api-key'])
        TestSetup.selenium = webdriver.Remote(command_executor=executor,
                                              desired_capabilities=capabilities)
    else:
        profile = _create_firefox_profile(item.config.option.firefox_preferences)
        if item.config.option.driver.upper() == 'REMOTE':
            if item.config.option.chrome_options:
                capabilities = _create_chrome_options(item.config.option.chrome_options).to_capabilities()
            else:
                capabilities = getattr(webdriver.DesiredCapabilities, item.config.option.browser_name.upper())
            capabilities['version'] = item.config.option.browser_version
            capabilities['platform'] = item.config.option.platform.upper()
            if item.config.option.capabilities:
                capabilities.update(json.loads(item.config.option.capabilities))
            executor = 'http://%s:%s/wd/hub' % (item.config.option.host, item.config.option.port)
            try:
                TestSetup.selenium = webdriver.Remote(command_executor=executor,
                                                      desired_capabilities=capabilities,
                                                      browser_profile=profile)
            except AttributeError:
                valid_browsers = [attr for attr in dir(webdriver.DesiredCapabilities) if not attr.startswith('__')]
                raise AttributeError("Invalid browser name: '%s'. Valid options are: %s" % (item.config.option.browser_name, ', '.join(valid_browsers)))

        elif item.config.option.driver.upper() == 'CHROME':
            if item.config.option.chrome_path:
                if item.config.option.chrome_options:
                    options = _create_chrome_options(item.config.option.chrome_options)
                    TestSetup.selenium = webdriver.Chrome(executable_path=item.config.option.chrome_path,
                                                          chrome_options=options)
                else:
                    TestSetup.selenium = webdriver.Chrome(executable_path=item.config.option.chrome_path)
            else:
                if item.config.option.chrome_options:
                    options = _create_chrome_options(item.config.option.chrome_options)
                    TestSetup.selenium = webdriver.Chrome(chrome_options=options)
                else:
                    TestSetup.selenium = webdriver.Chrome()

        elif item.config.option.driver.upper() == 'FIREFOX':
            binary = hasattr(item, 'firefox_path') and FirefoxBinary(item.config.option.firefox_path) or None
            TestSetup.selenium = webdriver.Firefox(
                firefox_binary=binary,
                firefox_profile=profile)
        elif item.config.option.driver.upper() == 'IE':
            TestSetup.selenium = webdriver.Ie()
        else:
            getattr(webdriver, item.config.option.driver)()

    TestSetup.selenium.implicitly_wait(TestSetup.default_implicit_wait)


def _start_rc_client(item):
    if item.config.option.sauce_labs_credentials_file:
        settings = _get_common_sauce_settings(item)
        settings.update({'username': item.sauce_labs_credentials['username'],
                         'access-key': item.sauce_labs_credentials['api-key'],
                         'os': item.config.option.browser_name,
                         'browser': item.config.option.browser_name,
                         'browser-version': item.config.option.browser_name})
        TestSetup.selenium = selenium('ondemand.saucelabs.com', '80',
                                      json.dumps(settings),
                                      TestSetup.base_url)
    else:
        browser = item.config.option.environment or item.config.option.browser
        TestSetup.selenium = selenium(item.config.option.host, str(item.config.option.port), browser, TestSetup.base_url)

    if item.config.option.capture_network:
        TestSetup.selenium.start("captureNetworkTraffic=true")
    else:
        TestSetup.selenium.start()

    TestSetup.selenium.set_timeout(TestSetup.timeout)
    TestSetup.selenium.set_context(".".join(split_class_and_test_names(item.nodeid)))


def _capture_session_id(item):
    if item.config.option.api.upper() == 'WEBDRIVER':
        session_id = TestSetup.selenium.session_id
    else:
        session_id = TestSetup.selenium.get_eval('selenium.sessionId')
    item.session_id = session_id


def _capture_screenshot(item):
    if item.config.option.api.upper() == 'WEBDRIVER':
        screenshot = TestSetup.selenium.get_screenshot_as_base64()
    else:
        screenshot = TestSetup.selenium.capture_entire_page_screenshot_to_string('')
    item.debug['screenshots'].append(screenshot)


def _capture_html(item):
    if item.config.option.api.upper() == 'WEBDRIVER':
        html = TestSetup.selenium.page_source
    else:
        html = TestSetup.selenium.get_html_source()
    if html:
        item.debug['html'].append(html.encode('utf-8'))


def _capture_log(item):
    if item.config.option.api.upper() == 'RC':
        log = TestSetup.selenium.get_log().encode('utf-8')
        item.debug['logs'].append(log)


def _capture_network_traffic(item):
    if item.config.option.api.upper() == 'RC' and item.config.option.capture_network:
        network_traffic = TestSetup.selenium.captureNetworkTraffic('json')
        item.debug['network_traffic'].append(network_traffic)


def _capture_url(item):
    if item.config.option.api.upper() == 'WEBDRIVER':
        url = TestSetup.selenium.current_url
    else:
        url = TestSetup.selenium.get_location()
    item.debug['urls'].append(url)


def _stop_selenium(item):
    if item.config.option.api == 'webdriver':
        try:
            TestSetup.selenium.quit()
        except:
            pass
    else:
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
