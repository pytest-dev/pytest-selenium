#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os

import pytest
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver


class Client(object):

    def __init__(self, test_id, options, keywords):
        self.test_id = test_id
        self.options = options
        self.keywords = keywords

        self.cloud = None
        self.host = options.host
        self.port = options.port
        self.base_url = options.base_url

        self.driver = options.driver
        self.capabilities = options.capabilities or []
        self.chrome_path = options.chrome_path
        self.chrome_options = options.chrome_options or '{}'
        self.firefox_path = options.firefox_path
        self.firefox_preferences = options.firefox_preferences or []
        self.profile_path = options.profile_path
        self.extension_paths = options.extension_paths or []
        self.opera_path = options.opera_path
        self.timeout = options.webqatimeout

        if self.driver.upper() == 'REMOTE':
            self.browser_name = options.browser_name
            self.browser_version = options.browser_version
            self.platform = options.platform

        if options.event_listener:
            mod_name, class_name = options.event_listener.rsplit('.', 1)
            mod = __import__(mod_name, fromlist=[class_name])
            self.event_listener = getattr(mod, class_name)
        else:
            self.event_listener = None

        self.default_implicit_wait = 10
        self.assume_untrusted = options.assume_untrusted
        self.proxy_host = options.proxy_host
        self.proxy_port = options.proxy_port

    def check_usage(self):
        if not self.base_url:
            raise pytest.UsageError('--baseurl must be specified.')

        if self.driver.upper() == 'REMOTE':
            if not self.browser_name:
                raise pytest.UsageError("--browsername must be specified.")

            if not self.platform:
                raise pytest.UsageError("--platform must be specified.")

    def start(self):
        self.check_usage()
        self.start_client()
        self.selenium.implicitly_wait(self.default_implicit_wait)

    def start_client(self):
        capabilities = {}
        for c in self.capabilities:
            name, value = c.split(':')
            # handle integer capabilities
            if value.isdigit():
                value = int(value)
            # handle boolean capabilities
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            capabilities.update({name: value})
        if self.proxy_host and self.proxy_port:
            proxy = Proxy()
            proxy.http_proxy = '%s:%s' % (self.proxy_host, self.proxy_port)
            proxy.ssl_proxy = proxy.http_proxy
            proxy.add_to_capabilities(capabilities)
        profile = None

        if self.driver.upper() == 'REMOTE':
            capabilities.update(getattr(webdriver.DesiredCapabilities, self.browser_name.upper()))
            if json.loads(self.chrome_options) or self.extension_paths:
                capabilities = self.create_chrome_options(
                    self.chrome_options,
                    self.extension_paths).to_capabilities()
            if self.browser_name.upper() == 'FIREFOX':
                profile = self.create_firefox_profile(
                    self.firefox_preferences,
                    self.profile_path,
                    self.extension_paths)
            if self.browser_version:
                capabilities['version'] = self.browser_version
            capabilities['platform'] = self.platform.upper()
            executor = 'http://%s:%s/wd/hub' % (self.host, self.port)
            try:
                self.selenium = webdriver.Remote(command_executor=executor,
                                                 desired_capabilities=capabilities or None,
                                                 browser_profile=profile)
            except AttributeError:
                valid_browsers = [attr for attr in dir(webdriver.DesiredCapabilities) if not attr.startswith('__')]
                raise AttributeError("Invalid browser name: '%s'. Valid options are: %s" % (self.browser_name, ', '.join(valid_browsers)))

        elif self.driver.upper() == 'CHROME':
            options = None
            if self.chrome_options or self.extension_paths:
                options = self.create_chrome_options(
                    self.chrome_options,
                    self.extension_paths)
            if self.chrome_path:
                self.selenium = webdriver.Chrome(executable_path=self.chrome_path,
                                                 chrome_options=options,
                                                 desired_capabilities=capabilities or None)
            else:
                self.selenium = webdriver.Chrome(chrome_options=options,
                                                 desired_capabilities=capabilities or None)

        elif self.driver.upper() == 'FIREFOX':
            binary = self.firefox_path and FirefoxBinary(self.firefox_path) or None
            profile = self.create_firefox_profile(
                self.firefox_preferences,
                self.profile_path,
                self.extension_paths)
            self.selenium = webdriver.Firefox(
                firefox_binary=binary,
                firefox_profile=profile,
                capabilities=capabilities or None)
        elif self.driver.upper() == 'IE':
            self.selenium = webdriver.Ie()
        elif self.driver.upper() == 'PHANTOMJS':
            self.selenium = webdriver.PhantomJS()
        elif self.driver.upper() == 'OPERA':
            capabilities.update(webdriver.DesiredCapabilities.OPERA)
            self.selenium = webdriver.Opera(executable_path=self.opera_path,
                                            desired_capabilities=capabilities)
        elif self.driver.upper() == 'BROWSERSTACK':
            # TODO support reading configuration from .browserstack
            from cloud import BrowserStack
            username = os.getenv('BROWSERSTACK_USERNAME')
            access_key = os.getenv('BROWSERSTACK_ACCESS_KEY')
            self.cloud = BrowserStack(username, access_key)
            self.selenium = self.cloud.driver(self.test_id, capabilities, self.options)
        elif self.driver.upper() == 'SAUCELABS':
            # TODO support reading configuration from .saucelabs
            from cloud import SauceLabs
            for v in ['SAUCELABS_USERNAME', 'SAUCELABS_API_KEY']:
                if v not in os.environ:
                    raise ValueError('Mandatory environment variable undefined: %s' % v)
            username = os.environ['SAUCELABS_USERNAME']
            api_key = os.environ['SAUCELABS_API_KEY']
            self.cloud = SauceLabs(username, api_key)
            self.selenium = self.cloud.driver(self.test_id, capabilities, self.options, self.keywords)
        else:
            self.selenium = getattr(webdriver, self.driver)()

        if self.event_listener is not None and not isinstance(self.selenium, EventFiringWebDriver):
            self.selenium = EventFiringWebDriver(self.selenium, self.event_listener())

    @property
    def session_id(self):
        return self.selenium.session_id

    def create_firefox_profile(self, preferences, profile_path, extensions):
        profile = webdriver.FirefoxProfile(profile_path)
        for p in preferences:
            name, value = p.split(':')
            # handle integer preferences
            if value.isdigit():
                value = int(value)
            # handle boolean preferences
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            profile.set_preference(name, value)
        profile.assume_untrusted_cert_issuer = self.assume_untrusted
        profile.update_preferences()
        for extension in extensions:
            profile.add_extension(extension)
        return profile

    def create_chrome_options(self, preferences, extensions):
        options = webdriver.ChromeOptions()
        options_from_json = json.loads(preferences)

        if 'arguments' in options_from_json:
            for args_ in options_from_json['arguments']:
                options.add_argument(args_)

        if 'binary_location' in options_from_json:
            options.binary_location = options_from_json['binary_location']

        for extension in extensions:
            options.add_extension(extension)

        return options
