# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest
from selenium.webdriver.support.event_firing_webdriver import \
    EventFiringWebDriver
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver


def proxy_from_options(options):
    if options.proxy_host and options.proxy_port:
        proxy_str = '%(proxy_host)s:%(proxy_port)s' % vars(options)
        proxy = Proxy()
        proxy.ssl_proxy = proxy.http_proxy = proxy_str
        return proxy


def make_driver(item):
    options = item.config.option
    capabilities = {}
    if options.capabilities is not None:
        for c in options.capabilities:
            name, value = c.split(':')
            # handle integer capabilities
            if value.isdigit():
                value = int(value)
            # handle boolean capabilities
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            capabilities[name] = value
    proxy = proxy_from_options(options)
    if proxy is not None:
        proxy.add_to_capabilities(capabilities)
    return start_driver(item, options, capabilities)


def start_driver(item, options, capabilities):
    specific_driver = '%s_driver' % options.driver.lower()
    driver_method = globals().get(specific_driver, generic_driver)
    driver = driver_method(item, options, capabilities)
    if options.event_listener is not None:
        mod_name, class_name = options.event_listener.rsplit('.', 1)
        mod = __import__(mod_name, fromlist=[class_name])
        event_listener = getattr(mod, class_name)
        if not isinstance(driver, EventFiringWebDriver):
            driver = EventFiringWebDriver(driver, event_listener())
    return driver


def generic_driver(item, options, capabilities):
    return getattr(webdriver, options.driver)()


def browserstack_driver(item, options, capabilities):
    from cloud import browserstack
    return browserstack.start_driver(item, options, capabilities)


def chrome_driver(item, options, capabilities):
    chrome_options = _create_chrome_options(options)
    extra = {}
    if options.chrome_path:
        extra['executable_path'] = options.chrome_path
    return webdriver.Chrome(
        chrome_options=chrome_options,
        desired_capabilities=capabilities or None,
        **extra)


def firefox_driver(item, options, capabilities):
    if options.firefox_path:
        binary = FirefoxBinary(options.firefox_path)
    else:
        binary = None
    profile = _create_firefox_profile(options)
    return webdriver.Firefox(
        firefox_binary=binary,
        firefox_profile=profile,
        capabilities=capabilities or None)


def ie_driver(item, options, capabilities):
    return webdriver.Ie()


def opera_driver(item, options, capabilities):
    capabilities.update(webdriver.DesiredCapabilities.OPERA)
    return webdriver.Opera(
        executable_path=options.opera_path,
        desired_capabilities=capabilities)


def phantomjs_driver(item, options, capabilities):
    return webdriver.PhantomJS()


def remote_driver(item, options, capabilities):
    if not options.browser_name:
        raise pytest.UsageError(
            '--browsername must be specified when using a server.')

    if not options.platform:
        raise pytest.UsageError(
            '--platform must be specified when using a server.')

    capabilities.update(getattr(webdriver.DesiredCapabilities,
                                options.browser_name.upper()))
    if json.loads(options.chrome_options) or options.extension_paths:
        capabilities = _create_chrome_options(options).to_capabilities()
    if options.browser_name.lower() == 'firefox':
        profile = _create_firefox_profile(options)
    if options.browser_version:
        capabilities['version'] = options.browser_version
    capabilities['platform'] = options.platform.upper()
    executor = 'http://%s:%s/wd/hub' % (options.host, options.port)
    try:
        return webdriver.Remote(
            command_executor=executor,
            desired_capabilities=capabilities or None,
            browser_profile=profile)
    except AttributeError:
        valid_browsers = [
            attr for attr in dir(webdriver.DesiredCapabilities)
            if not attr.startswith('__')
        ]
        raise AttributeError(
            "Invalid browser name: '%s'. Valid options are: %s" %
            (options.browser_name, ', '.join(valid_browsers)))


def saucelabs_driver(item, options, capabilities):
    from cloud import saucelabs
    return saucelabs.start_driver(item, options, capabilities)


def _create_chrome_options(options):
    chrome_options = webdriver.ChromeOptions()
    if options.chrome_options is None:
        return chrome_options
    options_from_json = json.loads(options.chrome_options)
    if 'arguments' in options_from_json:
        for args_ in options_from_json['arguments']:
            chrome_options.add_argument(args_)
    if 'binary_location' in options_from_json:
        chrome_options.binary_location = options_from_json['binary_location']
    if options.extension_paths is not None:
        for extension in options.extension_paths:
            chrome_options.add_extension(extension)
    return chrome_options


def _create_firefox_profile(options):
    profile = webdriver.FirefoxProfile(options.profile_path)
    if options.firefox_preferences is not None:
        for p in options.firefox_preferences:
            name, value = p.split(':')
            # handle integer preferences
            if value.isdigit():
                value = int(value)
            # handle boolean preferences
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            profile.set_preference(name, value)
    profile.assume_untrusted_cert_issuer = options.assume_untrusted
    profile.update_preferences()
    if options.extension_paths is not None:
        for extension in options.extension_paths:
            profile.add_extension(extension)
    return profile
