# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest
import requests

from . import cloud

REQUESTS_TIMEOUT = 10
SUPPORTED_DRIVERS = [
    'BrowserStack',
    'Chrome',
    'Firefox',
    'IE',
    'PhantomJS',
    'Remote',
    'SauceLabs']


@pytest.fixture(autouse=True)
def environment(request, base_url, capabilities):
    """Provide environment details to pytest-html report"""
    config = request.config
    if hasattr(config, '_html'):
        config._html.environment.append({
            'Base URL': base_url,
            'Capabilities': capabilities,
            'Driver': config.option.driver})
        if not hasattr(cloud, config.option.driver.lower()):
            config._html.environment.append({
                'Server': 'http://{0.host}:{0.port}'.format(config.option)})


@pytest.fixture(scope='session')
def base_url(request):
    config = request.config
    url = config.option.base_url or config.getini('selenium_base_url')
    if not url:
        raise pytest.UsageError('--base-url must be specified.')
    return url


@pytest.fixture(scope='session', autouse=True)
def _verify_base_url(request, base_url):
    if base_url:
        response = requests.get(base_url, timeout=REQUESTS_TIMEOUT)
        if response.status_code not in (200, 401):
            raise pytest.UsageError(
                'Base URL did not return status code 200 or 401. '
                '(URL: %s, Response: %s, Headers: %s)' % (
                    base_url, response.status_code, response.headers))


@pytest.fixture
def capabilities(request, variables):
    capabilities = variables.get('capabilities', {})
    for capability in request.config.option.capabilities:
        capabilities[capability[0]] = capability[1]
    return capabilities


@pytest.fixture
def driver(request, capabilities):
    from .driver import start_driver
    driver = start_driver(request.node, capabilities)
    request.node._driver = driver
    request.addfinalizer(lambda: driver.quit())
    return driver


@pytest.fixture
def selenium(_sensitive_skipping, driver):
    return driver


def pytest_runtest_makereport(__multicall__, item, call):
    pytest_html = item.config.pluginmanager.getplugin('html')
    extra_summary = []
    report = __multicall__.execute()
    extra = getattr(report, 'extra', [])
    if report.when == 'call':
        driver = getattr(item, '_driver', None)
        if driver is not None:
            xfail = hasattr(report, 'wasxfail')
            debug = (report.skipped and xfail) or (report.failed and not xfail)
            if debug:
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
                    if debug:
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
                     choices=SUPPORTED_DRIVERS,
                     dest='driver',
                     help='webdriver implementation.',
                     metavar='str')
    group._addoption('--capability',
                     action='append',
                     default=[],
                     dest='capabilities',
                     metavar=('key', 'value'),
                     nargs=2,
                     help='additional capabilities.')
    group._addoption('--firefox-path',
                     metavar='path',
                     help='path to the firefox binary.')
    group._addoption('--firefox-preference',
                     action='append',
                     default=[],
                     dest='firefox_preferences',
                     metavar=('name', 'value'),
                     nargs=2,
                     help='additional firefox preferences.')
    group._addoption('--firefox-profile',
                     metavar='path',
                     help='path to the firefox profile.')
    group._addoption('--firefox-extension',
                     action='append',
                     default=[],
                     dest='firefox_extensions',
                     metavar='path',
                     help='path to a firefox extension.')
    group._addoption('--event-listener',
                     action='store',
                     dest='event_listener',
                     metavar='str',
                     help='selenium eventlistener class, e.g. '
                          'package.module.EventListenerClassName.')
