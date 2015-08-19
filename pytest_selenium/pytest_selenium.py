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
    'SauceLabs',
    'TestingBot']


@pytest.fixture(scope='session', autouse=True)
def _environment(request, capabilities):
    """Provide additional environment details to pytest-html report"""
    config = request.config
    if hasattr(config, '_html'):
        # add environment details to the pytest-html plugin if possible
        environment = config._html.environment
        environment.append(('Driver', config.option.driver))
        # add capabilities to environment
        environment.extend([('Capability', '{0}: {1}'.format(
            k, v)) for k, v in capabilities.items()])
        if config.option.driver == 'Remote':
            environment.append(
                ('Server', 'http://{0.host}:{0.port}'.format(config.option)))


@pytest.fixture(scope='session')
def base_url(request):
    """Return a base URL"""
    config = request.config
    base_url = config.option.base_url or config.getini('base_url')
    if base_url:
        if hasattr(config, '_html'):
            config._html.environment.append(('Base URL', base_url))
        return base_url


@pytest.fixture(scope='session', autouse=True)
def _verify_url(request, base_url):
    """Verifies the base URL"""
    verify = request.config.option.verify_base_url
    if base_url and verify:
        response = requests.get(base_url, timeout=REQUESTS_TIMEOUT)
        if not response.status_code == requests.codes.ok:
            raise pytest.UsageError(
                'Base URL failed verification!'
                '\nURL: {0}, Response status code: {1.status_code}'
                '\nResponse headers: {1.headers}'.format(base_url, response))


@pytest.fixture(scope='session')
def capabilities(request, variables):
    """Returns combined capabilities from pytest-variables and command line"""
    capabilities = variables.get('capabilities', {})
    for capability in request.config.option.capabilities:
        capabilities[capability[0]] = capability[1]
    return capabilities


@pytest.fixture
def selenium(request, capabilities):
    """Returns a WebDriver instance based on options and capabilities"""
    from .driver import start_driver
    driver = start_driver(request.node, capabilities)
    request.node._driver = driver
    request.addfinalizer(lambda: driver.quit())
    return driver


def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave
    config.addinivalue_line(
        'markers', 'capabilities(kwargs): add or change existing '
        'capabilities. specify capabilities as keyword arguments, for example '
        'capabilities(foo=''bar'')')


def pytest_runtest_makereport(__multicall__, item, call):
    pytest_html = item.config.pluginmanager.getplugin('html')
    extra_summary = []
    report = __multicall__.execute()
    extra = getattr(report, 'extra', [])
    if report.when == 'call':
        driver = getattr(item, '_driver', None)
        if driver is not None:
            xfail = hasattr(report, 'wasxfail')
            # only gather debug if test failed or xfailed
            debug = (report.skipped and xfail) or (report.failed and not xfail)
            if debug:
                url = driver.current_url
                if url is not None:
                    # add failing url to the console output
                    extra_summary.append('Failing URL: {0}'.format(url))
                    if pytest_html is not None:
                        # add failing url to the html report
                        extra.append(pytest_html.extras.url(url))
                screenshot = driver.get_screenshot_as_base64()
                if screenshot is not None and pytest_html is not None:
                    # add screenshot to the html report
                    extra.append(pytest_html.extras.image(
                        screenshot, 'Screenshot'))
                html = driver.page_source.encode('utf-8')
                if html is not None and pytest_html is not None:
                    # add page source to the html report
                    extra.append(pytest_html.extras.text(html, 'HTML'))
            driver_name = item.config.option.driver
            if hasattr(cloud, driver_name.lower()) and driver.session_id:
                provider = getattr(cloud, driver_name.lower()).Provider()
                # add cloud job identifier to the console output
                job_url = provider.url(item.config, driver.session_id)
                extra_summary.append('{0} Job: {1}'.format(
                    provider.name, job_url))
                if pytest_html is not None:
                    # always add cloud job url to the html report
                    extra.append(pytest_html.extras.url(
                        job_url, '{0} Job'.format(provider.name)))
                    if debug:
                        # conditionally add cloud extras to html report
                        extra.append(pytest_html.extras.html(
                            provider.additional_html(driver.session_id)))
                passed = report.passed or (report.failed and xfail)
                # update job status with cloud provider
                provider.update_status(item.config, driver.session_id, passed)
        report.sections.append(('pytest-selenium', '\n'.join(extra_summary)))
        report.extra = extra
    return report


def pytest_addoption(parser):
    parser.addini('base_url', 'base url for selenium')

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

    # testingbot configuration
    parser.addini('testingbot_key',
                  help='testingbot key',
                  default=os.getenv('TESTINGBOT_KEY'))
    parser.addini('testingbot_secret',
                  help='testingbot secret',
                  default=os.getenv('TESTINGBOT_SECRET'))

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--base-url',
                     metavar='url',
                     help='base url for the application under test.')
    group._addoption('--verify-base-url',
                     action='store_true',
                     default=not os.getenv(
                         'VERIFY_BASE_URL', 'false').lower() == 'false',
                     help='verify the base url.')
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
    group._addoption('--driver',
                     choices=SUPPORTED_DRIVERS,
                     help='webdriver implementation.',
                     metavar='str')
    group._addoption('--driver-path',
                     metavar='path',
                     help='path to the driver executable.')
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
                     metavar='str',
                     help='selenium eventlistener class, e.g. '
                          'package.module.EventListenerClassName.')
