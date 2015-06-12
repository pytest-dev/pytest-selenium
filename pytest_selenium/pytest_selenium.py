# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

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
                'Driver Path': config.option.driver_path,
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
    config = request.config
    url = config.option.base_url or config.getini('selenium_base_url')
    if not url:
        raise pytest.UsageError('--base-url must be specified.')
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
                    provider.name, provider.url(
                        item.config, driver.session_id)))
                if pytest_html is not None:
                    extra.append(pytest_html.extras.url(
                        provider.url(item.config, driver.session_id),
                        '%s Job' % provider.name))
                    extra.append(pytest_html.extras.html(
                        provider.additional_html(driver.session_id)))
                passed = report.passed or (report.failed and xfail)
                provider.update_status(item.config, driver.session_id, passed)
        report.sections.append(('pytest-selenium', '\n'.join(extra_summary)))
        report.extra = extra
    return report


def pytest_addoption(parser):
    parser.addini('selenium_base_url', 'base url for selenium')

    # browserstack configuration
    parser.addini('browserstack_username',
                  help='browserstack username',
                  default=os.getenv('BROWSERSTACK_USERNAME'))
    parser.addini('browserstack_access_key',
                  help='browserstack access key',
                  default=os.getenv('BROWSERSTACK_ACCESS_KEY'))

    # sauce labs configuration
    parser.addini('sauce_labs_username',
                  help='sauce labs username',
                  default=os.getenv('SAUCELABS_USERNAME'))
    parser.addini('sauce_labs_api_key',
                  help='sauce labs api key',
                  default=os.getenv('SAUCELABS_API_KEY'))
    parser.addini('sauce_labs_job_visibility',
                  help='default visibility for jobs',
                  default='public restricted')
    parser.addini('sauce_labs_tags',
                  help='space separated tags for filtering and grouping',
                  type='args')

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--base-url',
                     action='store',
                     dest='base_url',
                     metavar='url',
                     help='base url for the application under test.')

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
    group._addoption('--driver-path',
                     action='store',
                     dest='driver_path',
                     metavar='path',
                     help='path to the driver.')
    group._addoption('--firefox-pref',
                     action='append',
                     dest='firefox_preferences',
                     metavar='str',
                     help='firefox preference name and value to set in format '
                          '"name:value".')
    group._addoption('--firefox-profile',
                     action='store',
                     dest='profile_path',
                     metavar='str',
                     help='path to the firefox profile to use.')
    group._addoption('--browser_extension',
                     action='append',
                     dest='extension_paths',
                     metavar='str',
                     help='path to browser extension to install.')
    group._addoption('--chrome-option',
                     action='append',
                     dest='chrome_option',
                     metavar='str',
                     help='google chrome option to set.')
    group._addoption('--webqatimeout',
                     action='store',
                     type='int',
                     default=60,
                     metavar='num',
                     help='timeout (in seconds) for page loads, etc. '
                          '(default: %default)')
    group._addoption('--proxy-host',
                     action='store',
                     dest='proxy_host',
                     metavar='str',
                     help='use a proxy running on this host.')
    group._addoption('--proxy-port',
                     action='store',
                     dest='proxy_port',
                     metavar='int',
                     help='use a proxy running on this port.')
    group._addoption('--event-listener',
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
