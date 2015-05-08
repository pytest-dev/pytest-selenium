#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re
import ConfigParser

import py
import pytest
import requests

import cloud
import credentials

__version__ = '2.0'
REQUESTS_TIMEOUT = 10


class DeferPlugin(object):
    """Simple plugin to defer pytest-html hook functions."""

    def pytest_html_environment(self, config):
        driver = config.option.driver
        if hasattr(cloud, driver.lower()):
            server = getattr(cloud, driver.lower()).name
        else:
            server = 'http://%s:%s' % (config.option.host,
                                       config.option.port)
        browser = config.option.browser_name and \
            config.option.browser_version and \
            config.option.platform and \
            '%s %s on %s' % (str(config.option.browser_name).title(),
                             config.option.browser_version,
                             str(config.option.platform).title())
        return {'Base URL': config.option.base_url,
                'Build': config.option.build,
                'Driver': config.option.driver,
                'Firefox Path': config.option.firefox_path,
                'Google Chrome Path': config.option.chrome_path,
                'Server': server,
                'Browser': browser,
                'Timeout': config.option.webqatimeout,
                'Credentials': config.option.credentials_file}


@pytest.mark.tryfirst
def pytest_configure(config):
    if config.pluginmanager.hasplugin('html'):
        config.pluginmanager.register(DeferPlugin())

    if not hasattr(config, 'slaveinput'):

        config.addinivalue_line(
            'markers', 'nondestructive: mark the test as nondestructive. '
            'Tests are assumed to be destructive unless this marker is '
            'present. This reduces the risk of running destructive tests '
            'accidentally.')

        if not config.option.run_destructive:
            if config.option.markexpr:
                config.option.markexpr = 'nondestructive and (%s)' % config.option.markexpr
            else:
                config.option.markexpr = 'nondestructive'


def pytest_sessionstart(session):
    if hasattr(session.config, 'slaveinput') or \
            session.config.option.skip_url_check or \
            session.config.option.collectonly:
        return

    if session.config.option.base_url:
        r = requests.get(session.config.option.base_url, verify=False, timeout=REQUESTS_TIMEOUT)
        assert r.status_code in (200, 401), ('Base URL did not return status code 200 or 401. '
                                             '(URL: %s, Response: %s, Headers: %s)' %
                                             (session.config.option.base_url, r.status_code, r.headers))

    # configure session proxies
    if hasattr(session.config, 'browsermob_session_proxy'):
        session.config.option.proxy_host = session.config.option.bmp_host
        session.config.option.proxy_port = session.config.browsermob_session_proxy.port

    if hasattr(session.config, 'zap'):
        if all([session.config.option.proxy_host, session.config.option.proxy_port]):
            session.config.zap.core.set_option_proxy_chain_name(session.config.option.proxy_host)
            session.config.zap.core.set_option_proxy_chain_port(session.config.option.proxy_port)
        session.config.option.proxy_host = session.config.option.zap_host
        session.config.option.proxy_port = session.config.option.zap_port


def pytest_runtest_setup(item):
    TestSetup.base_url = item.config.option.base_url

    # configure test proxies
    if hasattr(item.config, 'browsermob_test_proxy'):
        item.config.option.proxy_host = item.config.option.bmp_host
        item.config.option.proxy_port = item.config.browsermob_test_proxy.port

    # consider this environment sensitive if the base url or any redirection
    # history matches the regular expression
    sensitive = False
    if TestSetup.base_url and not item.config.option.skip_url_check:
        r = requests.get(TestSetup.base_url, verify=False, timeout=REQUESTS_TIMEOUT)
        urls = [h.url for h in r.history] + [r.url]
        matches = [re.search(item.config.option.sensitive_url, u) for u in urls]
        sensitive = any(matches)

    destructive = 'nondestructive' not in item.keywords

    if (sensitive and destructive):
        first_match = matches[next(i for i, match in enumerate(matches) if match)]

        # skip the test with an appropriate message
        py.test.skip('This test is destructive and the target URL is '
                     'considered a sensitive environment. If this test is '
                     'not destructive, add the \'nondestructive\' marker to '
                     'it. Sensitive URL: %s' % first_match.string)

    if item.config.option.credentials_file:
        TestSetup.credentials = credentials.read(item.config.option.credentials_file)

    test_id = '.'.join(split_class_and_test_names(item.nodeid))

    if 'skip_selenium' not in item.keywords:
        from selenium_client import Client
        TestSetup.selenium_client = Client(
            test_id,
            item.config.option,
            item.keywords)
        TestSetup.selenium_client.start()
        item.session_id = TestSetup.selenium_client.session_id
        TestSetup.selenium = TestSetup.selenium_client.selenium
        TestSetup.timeout = TestSetup.selenium_client.timeout
        TestSetup.default_implicit_wait = TestSetup.selenium_client.default_implicit_wait
    else:
        TestSetup.timeout = item.config.option.webqatimeout
        TestSetup.selenium = None


def pytest_runtest_teardown(item):
    if hasattr(TestSetup, 'selenium') and TestSetup.selenium and 'skip_selenium' not in item.keywords:
        TestSetup.selenium.quit()


def pytest_runtest_makereport(__multicall__, item, call):
    pytest_html = item.config.pluginmanager.getplugin('html')
    extra_summary = []
    report = __multicall__.execute()
    extra = getattr(report, 'extra', [])
    try:
        report.public = item.keywords['privacy'].args[0] == 'public'
    except (IndexError, KeyError):
        # privacy mark is not present or has no value
        report.public = False
    if report.when == 'call':
        report.session_id = getattr(item, 'session_id', None)
        if hasattr(TestSetup, 'selenium') and TestSetup.selenium and 'skip_selenium' not in item.keywords:
            xfail = hasattr(report, 'wasxfail')
            if (report.skipped and xfail) or (report.failed and not xfail):
                url = TestSetup.selenium.current_url
                if url is not None:
                    extra_summary.append('Failing URL: %s' % url)
                    if pytest_html is not None:
                        extra.append(pytest_html.extras.url(url))
                screenshot = TestSetup.selenium.get_screenshot_as_base64()
                if screenshot is not None and pytest_html is not None:
                    extra.append(pytest_html.extras.image(screenshot, 'Screenshot'))
                html = TestSetup.selenium.page_source.encode('utf-8')
                if html is not None and pytest_html is not None:
                    extra.append(pytest_html.extras.text(html, 'HTML'))
            if TestSetup.selenium_client.cloud is not None and report.session_id:
                cloud = TestSetup.selenium_client.cloud
                extra_summary.append('%s Job: %s' % (cloud.name, cloud.url(report.session_id)))
                if pytest_html is not None:
                    extra.append(pytest_html.extras.url(cloud.url, '%s Job' % cloud.name))
                    extra.append(pytest_html.extras.html(cloud.additional_html(report.session_id)))
                passed = report.passed or (report.failed and xfail)
                cloud.update_status(report.session_id, passed)
        report.sections.append(('pytest-mozwebqa', '\n'.join(extra_summary)))
        report.extra = extra
    return report


def pytest_funcarg__mozwebqa(request):
    return TestSetup(request)


def pytest_addoption(parser):
    config = ConfigParser.ConfigParser(defaults={'baseurl': ''})
    config.read('mozwebqa.cfg')

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--baseurl',
                     action='store',
                     dest='base_url',
                     default=config.get('DEFAULT', 'baseurl'),
                     metavar='url',
                     help='base url for the application under test.')
    group._addoption('--skipurlcheck',
                     action='store_true',
                     dest='skip_url_check',
                     default=False,
                     help='skip the base url and sensitivity checks. (default: %default)')
    group._addoption('--host',
                     action='store',
                     default=os.environ.get('SELENIUM_HOST', 'localhost'),
                     metavar='str',
                     help='host that selenium server is listening on. (default: %default)')
    group._addoption('--port',
                     action='store',
                     type='int',
                     default=os.environ.get('SELENIUM_PORT', 4444),
                     metavar='num',
                     help='port that selenium server is listening on. (default: %default)')
    group._addoption('--driver',
                     action='store',
                     dest='driver',
                     default=os.environ.get('SELENIUM_DRIVER', 'Remote'),
                     metavar='str',
                     help='webdriver implementation. (default: %default)')
    group._addoption('--capability',
                     action='append',
                     dest='capabilities',
                     metavar='str',
                     help='additional capability to set in format "name:value".')
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
                     action='append',
                     dest='firefox_preferences',
                     metavar='str',
                     help='firefox preference name and value to set in format "name:value".')
    group._addoption('--profilepath',
                     action='store',
                     dest='profile_path',
                     metavar='str',
                     help='path to the firefox profile to use.')
    group._addoption('--extension',
                     action='append',
                     dest='extension_paths',
                     metavar='str',
                     help='path to browser extension to install.')
    group._addoption('--chromeopts',
                     action='store',
                     dest='chrome_options',
                     metavar='str',
                     help='json string of google chrome options to set.')
    group._addoption('--operapath',
                     action='store',
                     dest='opera_path',
                     metavar='path',
                     help='path to the opera driver.')
    group._addoption('--browsername',
                     action='store',
                     dest='browser_name',
                     default=os.environ.get('SELENIUM_BROWSER'),
                     metavar='str',
                     help='target browser name (default: %default).')
    group._addoption('--browserver',
                     action='store',
                     dest='browser_version',
                     default=os.environ.get('SELENIUM_VERSION'),
                     metavar='str',
                     help='target browser version (default: %default).')
    group._addoption('--platform',
                     action='store',
                     default=os.environ.get('SELENIUM_PLATFORM'),
                     metavar='str',
                     help='target platform (default: %default).')
    group._addoption('--webqatimeout',
                     action='store',
                     type='int',
                     default=60,
                     metavar='num',
                     help='timeout (in seconds) for page loads, etc. (default: %default)')
    group._addoption('--build',
                     action='store',
                     dest='build',
                     metavar='str',
                     help='build identifier (for continuous integration).')
    group._addoption('--untrusted',
                     action='store_true',
                     dest='assume_untrusted',
                     default=False,
                     help='assume that all certificate issuers are untrusted. (default: %default)')
    group._addoption('--proxyhost',
                     action='store',
                     dest='proxy_host',
                     metavar='str',
                     help='use a proxy running on this host.')
    group._addoption('--proxyport',
                     action='store',
                     dest='proxy_port',
                     metavar='int',
                     help='use a proxy running on this port.')
    group._addoption('--eventlistener',
                     action='store',
                     dest='event_listener',
                     metavar='str',
                     help='selenium eventlistener class, e.g. package.module.EventListenerClassName.')

    group = parser.getgroup('safety', 'safety')
    group._addoption('--sensitiveurl',
                     action='store',
                     dest='sensitive_url',
                     default='(firefox\.com)|(mozilla\.(com|org))',
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


def split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
