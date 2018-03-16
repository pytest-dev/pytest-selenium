# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import copy
from datetime import datetime
import os
import io

import pytest
from requests.structures import CaseInsensitiveDict
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.event_firing_webdriver import \
    EventFiringWebDriver

from . import drivers

SUPPORTED_DRIVERS = CaseInsensitiveDict({
    'BrowserStack': webdriver.Remote,
    'CrossBrowserTesting': webdriver.Remote,
    'Chrome': webdriver.Chrome,
    'Edge': webdriver.Edge,
    'Firefox': webdriver.Firefox,
    'IE': webdriver.Ie,
    'PhantomJS': webdriver.PhantomJS,
    'Remote': webdriver.Remote,
    'Safari': webdriver.Safari,
    'SauceLabs': webdriver.Remote,
    'TestingBot': webdriver.Remote})


def pytest_addhooks(pluginmanager):
    from . import hooks
    method = getattr(pluginmanager, 'add_hookspecs', None)
    if method is None:
        method = pluginmanager.addhooks
    method(hooks)


@pytest.fixture(scope='session')
def session_capabilities(pytestconfig):
    """Returns combined capabilities from pytest-variables and command line"""
    driver = pytestconfig.getoption('driver').upper()
    capabilities = getattr(DesiredCapabilities, driver, {}).copy()
    if driver == 'REMOTE':
        browser = capabilities.get('browserName', '').upper()
        capabilities.update(getattr(DesiredCapabilities, browser, {}))
    capabilities.update(pytestconfig._capabilities)
    return capabilities


@pytest.fixture
def capabilities(request, driver_class, chrome_options, firefox_options,
                 session_capabilities):
    """Returns combined capabilities"""
    capabilities = copy.deepcopy(session_capabilities)  # make a copy
    if driver_class == webdriver.Remote:
        browser = capabilities.get('browserName', '').upper()
        key, options = (None, None)
        if browser == 'CHROME':
            key = getattr(chrome_options, 'KEY', 'goog:chromeOptions')
            options = chrome_options.to_capabilities()
            if key not in options:
                key = 'chromeOptions'
        elif browser == 'FIREFOX':
            key = firefox_options.KEY
            options = firefox_options.to_capabilities()
        if all([key, options]):
            capabilities.setdefault(key, {}).update(options.get(key, {}))
    capabilities_marker = request.node.get_marker('capabilities')
    if capabilities_marker is not None:
        # add capabilities from the marker
        capabilities.update(capabilities_marker.kwargs)
    return capabilities


@pytest.fixture
def driver_args():
    """Return arguments to pass to the driver service"""
    return None


@pytest.fixture
def driver_kwargs(request, capabilities, chrome_options, driver_args,
                  driver_class, driver_log, driver_path, firefox_options,
                  firefox_profile, pytestconfig):
    kwargs = {}
    driver = getattr(drivers, pytestconfig.getoption('driver').lower())
    kwargs.update(driver.driver_kwargs(
        capabilities=capabilities,
        chrome_options=chrome_options,
        driver_args=driver_args,
        driver_log=driver_log,
        driver_path=driver_path,
        firefox_options=firefox_options,
        firefox_profile=firefox_profile,
        host=pytestconfig.getoption('host'),
        port=pytestconfig.getoption('port'),
        request=request,
        log_path=None,
        test='.'.join(split_class_and_test_names(request.node.nodeid))))
    pytestconfig._driver_log = driver_log
    return kwargs


@pytest.fixture
def driver_class(request):
    driver = request.config.getoption('driver')
    if driver is None:
        raise pytest.UsageError('--driver must be specified')
    return SUPPORTED_DRIVERS[driver]


@pytest.fixture
def driver_log(tmpdir):
    """Return path to driver log"""
    return str(tmpdir.join('driver.log'))


@pytest.fixture
def driver_path(request):
    return request.config.getoption('driver_path')


@pytest.yield_fixture
def driver(request, driver_class, driver_kwargs):
    """Returns a WebDriver instance based on options and capabilities"""
    driver = driver_class(**driver_kwargs)

    event_listener = request.config.getoption('event_listener')
    if event_listener is not None:
        # Import the specified event listener and wrap the driver instance
        mod_name, class_name = event_listener.rsplit('.', 1)
        mod = __import__(mod_name, fromlist=[class_name])
        event_listener = getattr(mod, class_name)
        if not isinstance(driver, EventFiringWebDriver):
            driver = EventFiringWebDriver(driver, event_listener())

    request.node._driver = driver
    yield driver
    driver.quit()


@pytest.yield_fixture
def selenium(driver):
    yield driver


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    capabilities = config._variables.get('capabilities', {})
    capabilities.update({k: v for k, v in config.getoption('capabilities')})
    config.addinivalue_line(
        'markers', 'capabilities(kwargs): add or change existing '
        'capabilities. specify capabilities as keyword arguments, for example '
        'capabilities(foo=''bar'')')
    if hasattr(config, '_metadata'):
        config._metadata['Driver'] = config.getoption('driver')
        config._metadata['Capabilities'] = capabilities
        if all((config.getoption('host'), config.getoption('port'))):
            config._metadata['Server'] = '{0}:{1}'.format(
                config.getoption('host'),
                config.getoption('port'))
    config._capabilities = capabilities


def pytest_report_header(config, startdir):
    driver = config.getoption('driver')
    if driver is not None:
        return 'driver: {0}'.format(driver)


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    summary = []
    extra = getattr(report, 'extra', [])
    driver = getattr(item, '_driver', None)
    xfail = hasattr(report, 'wasxfail')
    failure = (report.skipped and xfail) or (report.failed and not xfail)
    when = item.config.getini('selenium_capture_debug').lower()
    capture_debug = when == 'always' or (when == 'failure' and failure)
    if capture_debug:
        exclude = item.config.getini('selenium_exclude_debug').lower()
        if 'logs' not in exclude:
            # gather logs that do not depend on a driver instance
            _gather_driver_log(item, summary, extra)
        if driver is not None:
            # gather debug that depends on a driver instance
            if 'url' not in exclude:
                _gather_url(item, report, driver, summary, extra)
            if 'screenshot' not in exclude:
                _gather_screenshot(item, report, driver, summary, extra)
            if 'html' not in exclude:
                _gather_html(item, report, driver, summary, extra)
            if 'logs' not in exclude:
                _gather_logs(item, report, driver, summary, extra)
            # gather debug from hook implementations
            item.config.hook.pytest_selenium_capture_debug(
                item=item, report=report, extra=extra)
    if driver is not None:
        # allow hook implementations to further modify the report
        item.config.hook.pytest_selenium_runtest_makereport(
            item=item, report=report, summary=summary, extra=extra)
    if summary:
        report.sections.append(('pytest-selenium', '\n'.join(summary)))
    report.extra = extra


def _gather_url(item, report, driver, summary, extra):
    try:
        url = driver.current_url
    except Exception as e:
        summary.append('WARNING: Failed to gather URL: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # add url to the html report
        extra.append(pytest_html.extras.url(url))
    summary.append('URL: {0}'.format(url))


def _gather_screenshot(item, report, driver, summary, extra):
    try:
        screenshot = driver.get_screenshot_as_base64()
    except Exception as e:
        summary.append('WARNING: Failed to gather screenshot: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # add screenshot to the html report
        extra.append(pytest_html.extras.image(screenshot, 'Screenshot'))


def _gather_html(item, report, driver, summary, extra):
    try:
        html = driver.page_source
    except Exception as e:
        summary.append('WARNING: Failed to gather HTML: {0}'.format(e))
        return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # add page source to the html report
        extra.append(pytest_html.extras.text(html, 'HTML'))


def _gather_logs(item, report, driver, summary, extra):
    pytest_html = item.config.pluginmanager.getplugin('html')
    try:
        types = driver.log_types
    except Exception as e:
        # note that some drivers may not implement log types
        summary.append('WARNING: Failed to gather log types: {0}'.format(e))
        return
    for name in types:
        try:
            log = driver.get_log(name)
        except Exception as e:
            summary.append('WARNING: Failed to gather {0} log: {1}'.format(
                name, e))
            return
        if pytest_html is not None:
            extra.append(pytest_html.extras.text(
                format_log(log), '%s Log' % name.title()))


def _gather_driver_log(item, summary, extra):
    pytest_html = item.config.pluginmanager.getplugin('html')
    if hasattr(item.config, '_driver_log') and \
       os.path.exists(item.config._driver_log):
        if pytest_html is not None:
            with io.open(item.config._driver_log, 'r', encoding='utf8') as f:
                extra.append(pytest_html.extras.text(f.read(), 'Driver Log'))
            summary.append('Driver log: {0}'.format(item.config._driver_log))


def format_log(log):
    timestamp_format = '%Y-%m-%d %H:%M:%S.%f'
    entries = [u'{0} {1[level]} - {1[message]}'.format(
        datetime.utcfromtimestamp(entry['timestamp'] / 1000.0).strftime(
            timestamp_format), entry).rstrip() for entry in log]
    log = '\n'.join(entries)
    return log


def split_class_and_test_names(nodeid):
    """Returns the class and method name from the current test"""
    names = nodeid.split('::')
    names[0] = names[0].replace('/', '.')
    names = [x.replace('.py', '') for x in names if x != '()']
    classnames = names[:-1]
    classname = '.'.join(classnames)
    name = names[-1]
    return classname, name


class DriverAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        driver = getattr(drivers, values.lower())
        # set the default host and port if specified in the driver module
        namespace.host = namespace.host or getattr(driver, 'HOST', None)
        namespace.port = namespace.port or getattr(driver, 'PORT', None)


def pytest_addoption(parser):
    _capture_choices = ('never', 'failure', 'always')
    parser.addini('selenium_capture_debug',
                  help='when debug is captured {0}'.format(_capture_choices),
                  default=os.getenv('SELENIUM_CAPTURE_DEBUG', 'failure'))
    parser.addini('selenium_exclude_debug',
                  help='debug to exclude from capture',
                  default=os.getenv('SELENIUM_EXCLUDE_DEBUG'))

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--driver',
                     action=DriverAction,
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
    group._addoption('--event-listener',
                     metavar='str',
                     help='selenium eventlistener class, e.g. '
                          'package.module.EventListenerClassName.')
    group._addoption('--host',
                     metavar='str',
                     help='host that the selenium server is listening on, '
                          'which will default to the cloud provider default '
                          'or localhost.')
    group._addoption('--port',
                     type=int,
                     metavar='num',
                     help='port that the selenium server is listening on, '
                          'which will default to the cloud provider default '
                          'or localhost.')
