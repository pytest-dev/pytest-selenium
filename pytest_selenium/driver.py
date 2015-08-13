# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from selenium.webdriver.support.event_firing_webdriver import \
    EventFiringWebDriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver


def start_driver(item, capabilities):
    options = item.config.option
    if options.driver is None:
        raise pytest.UsageError('--driver must be specified')
    driver = globals().get(
        '%s_driver' % options.driver.lower())(item, capabilities)
    if options.event_listener is not None:
        mod_name, class_name = options.event_listener.rsplit('.', 1)
        mod = __import__(mod_name, fromlist=[class_name])
        event_listener = getattr(mod, class_name)
        if not isinstance(driver, EventFiringWebDriver):
            driver = EventFiringWebDriver(driver, event_listener())
    return driver


def browserstack_driver(item, capabilities):
    """Return a WebDriver using a BrowserStack instance"""
    from .cloud.browserstack import Provider
    return Provider().start_driver(item, capabilities)


def chrome_driver(item, capabilities):
    return webdriver.Chrome(desired_capabilities=capabilities)


def firefox_driver(item, capabilities):
    options = item.config.option
    binary = None
    if options.firefox_path:
        binary = FirefoxBinary(options.firefox_path)
    profile = _create_firefox_profile(options)
    return webdriver.Firefox(
        firefox_binary=binary,
        firefox_profile=profile,
        capabilities=capabilities or None)


def ie_driver(item, capabilities):
    return webdriver.Ie(capabilities=capabilities)


def phantomjs_driver(item, capabilities):
    return webdriver.PhantomJS(desired_capabilities=capabilities)


def remote_driver(item, capabilities):
    options = item.config.option
    if 'browserName' not in capabilities:
        raise pytest.UsageError('The \'browserName\' capability must be '
                                'specified when using the remote driver.')
    capabilities.setdefault('version', '')
    capabilities.setdefault('platform', 'ANY')
    executor = 'http://%s:%s/wd/hub' % (options.host, options.port)
    return webdriver.Remote(
        command_executor=executor,
        desired_capabilities=capabilities,
        browser_profile=_create_firefox_profile(options))


def saucelabs_driver(item, capabilities):
    """Return a WebDriver using a Sauce Labs instance"""
    from .cloud.saucelabs import Provider
    return Provider().start_driver(item, capabilities)


def _create_firefox_profile(options):
    profile = webdriver.FirefoxProfile(options.firefox_profile)
    for preference in options.firefox_preferences:
        name, value = preference
        # handle integer preferences
        if value.isdigit():
            value = int(value)
        # handle boolean preferences
        elif value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        profile.set_preference(name, value)
    profile.update_preferences()
    for extension in options.firefox_extensions:
        profile.add_extension(extension)
    return profile
