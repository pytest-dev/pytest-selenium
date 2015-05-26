# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import ConfigParser

import pytest
import requests

import cloud

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
                'Timeout': config.option.webqatimeout}


@pytest.mark.tryfirst
def pytest_configure(config):
    if config.pluginmanager.hasplugin('html'):
        config.pluginmanager.register(DeferPlugin())


def pytest_sessionstart(session):
    # configure session proxies
    option = session.config.option
    if hasattr(session.config, 'browsermob_session_proxy'):
        option.proxy_host = option.bmp_host
        option.proxy_port = session.config.browsermob_session_proxy.port

    zap = getattr(session.config, 'zap', None)
    if zap is not None:
        if option.proxy_host and option.proxy_port:
            zap.core.set_option_proxy_chain_name(option.proxy_host)
            zap.core.set_option_proxy_chain_port(option.proxy_port)
        option.proxy_host = option.zap_host
        option.proxy_port = option.zap_port


@pytest.fixture(scope='session')
def base_url(request):
    url = request.config.option.base_url
    if not url:
        raise pytest.UsageError('--baseurl must be specified.')
    return url


@pytest.fixture(scope='session', autouse=True)
def _verify_base_url(request, base_url):
    option = request.config.option
    if base_url and not option.skip_url_check:
        response = requests.get(base_url, timeout=REQUESTS_TIMEOUT)
        if response.status_code not in (200, 401):
            raise pytest.UsageError(
                'Base URL did not return status code 200 or 401. '
                '(URL: %s, Response: %s, Headers: %s)' % (
                    base_url, response.status_code, response.headers))


@pytest.fixture
def driver(request):
    from .driver import make_driver

    driver = make_driver(request.node)
    request.node._driver = driver
    request.addfinalizer(lambda: driver.quit())
    return driver


@pytest.fixture
def mozwebqa(request, _sensitive_skipping, driver, base_url):
    return TestSetup(request, driver, base_url)


def pytest_runtest_setup(item):
    # configure test proxies
    option = item.config.option
    if hasattr(item.config, 'browsermob_test_proxy'):
        option.proxy_host = item.config.option.bmp_host
        option.proxy_port = item.config.browsermob_test_proxy.port


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
        driver = getattr(item, '_driver', None)
        if driver is not None:
            xfail = hasattr(report, 'wasxfail')
            if (report.skipped and xfail) or (report.failed and not xfail):
                url = driver.current_url
                if url is not None:
                    extra_summary.append('Failing URL: %s' % url)
                    if pytest_html is not None:
                        extra.append(pytest_html.extras.url(url))
                screenshot = driver.get_screenshot_as_base64()
                if screenshot is not None and pytest_html is not None:
                    extra.append(pytest_html.extras.image(
                        screenshot, 'Screenshot'))
                html = driver.page_source.encode('utf-8')
                if html is not None and pytest_html is not None:
                    extra.append(pytest_html.extras.text(html, 'HTML'))
            driver_name = item.config.option.driver
            if hasattr(cloud, driver_name.lower()) and driver.session_id:
                provider = getattr(cloud, driver_name.lower())
                extra_summary.append('%s Job: %s' % (
                    provider.name, provider.url(driver.session_id)))
                if pytest_html is not None:
                    extra.append(pytest_html.extras.url(
                        provider.url(driver.session_id),
                        '%s Job' % provider.name))
                    extra.append(pytest_html.extras.html(
                        provider.additional_html(driver.session_id)))
                passed = report.passed or (report.failed and xfail)
                provider.update_status(driver.session_id, passed)
        report.sections.append(('pytest-selenium', '\n'.join(extra_summary)))
        report.extra = extra
    return report


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
                     help='skip the base url and sensitivity checks. '
                          '(default: %default)')
    group._addoption('--host',
                     action='store',
                     default=os.environ.get('SELENIUM_HOST', 'localhost'),
                     metavar='str',
                     help='host that selenium server is listening on. '
                          '(default: %default)')
    group._addoption('--port',
                     action='store',
                     type='int',
                     default=os.environ.get('SELENIUM_PORT', 4444),
                     metavar='num',
                     help='port that selenium server is listening on. '
                          '(default: %default)')
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
                     help='additional capability to set in format '
                          '"name:value".')
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
                     help='firefox preference name and value to set in format '
                          '"name:value".')
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
                     help='timeout (in seconds) for page loads, etc. '
                          '(default: %default)')
    group._addoption('--build',
                     action='store',
                     dest='build',
                     metavar='str',
                     help='build identifier (for continuous integration).')
    group._addoption('--untrusted',
                     action='store_true',
                     dest='assume_untrusted',
                     default=False,
                     help='assume that all certificate issuers are untrusted. '
                          '(default: %default)')
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
                     help='selenium eventlistener class, e.g. '
                          'package.module.EventListenerClassName.')


class TestSetup:

    default_implicit_wait = 10

    def __init__(self, request, driver, base_url):
        self.request = request
        self.selenium = driver
        self.base_url = base_url

        self.timeout = request.node.config.option.webqatimeout
        self.selenium.implicitly_wait(self.default_implicit_wait)
