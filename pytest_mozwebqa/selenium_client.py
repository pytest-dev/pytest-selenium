#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import selenium
from selenium import webdriver


class Client(object):

    def __init__(self, test_id, options):
        self.test_id = test_id
        self.host = options.host
        self.port = options.port
        self.base_url = options.base_url
        self.api = options.api.upper()

        self.webdriver = self.api == 'WEBDRIVER'
        self.rc = self.api == 'RC'

        if self.webdriver:
            self.driver = options.driver
            self.capabilities = options.capabilities
            self.chrome_path = options.chrome_path
            self.chrome_options = options.chrome_options
            self.firefox_path = options.firefox_path
            self.firefox_preferences = options.firefox_preferences
            self.timeout = options.timeout

            if self.driver.upper() == 'REMOTE':
                self.browser_name = options.browser_name
                self.browser_version = options.browser_version
                self.platform = options.platform

        if self.rc:
            self.browser = options.environment or options.browser
            self.timeout = options.timeout * 1000

        self.capture_network = options.capture_network
        self.default_implicit_wait = 10
        self.sauce_labs_credentials = options.sauce_labs_credentials_file
        self.assume_untrusted = options.assume_untrusted

    def check_usage(self):
        self.check_basic_usage()

        if self.webdriver:
            self.check_webdriver_usage()
        else:
            self.check_rc_usage()

    def check_basic_usage(self):
        if not self.base_url:
            raise pytest.UsageError('--baseurl must be specified.')

    def check_webdriver_usage(self):
        if self.driver.upper() == 'REMOTE':
            if not self.browser_name:
                raise pytest.UsageError("--browsername must be specified when using the 'webdriver' api.")

            if not self.platform:
                raise pytest.UsageError("--platform must be specified when using the 'webdriver' api.")

    def check_rc_usage(self):
        if not self.browser:
            raise pytest.UsageError("--browser or --environment must be specified when using the 'rc' api.")

    def start(self):
        self.check_usage()
        if self.webdriver:
            self.start_webdriver_client()
            self.selenium.implicitly_wait(self.default_implicit_wait)
        else:
            self.start_rc_client()
            self.selenium.set_timeout(self.timeout)
            self.selenium.set_context(self.test_id)

    def start_webdriver_client(self):
        profile = self.create_firefox_profile(self.firefox_preferences)
        if self.driver.upper() == 'REMOTE':
            if self.chrome_options:
                capabilities = self.create_chrome_options(self.chrome_options).to_capabilities()
            else:
                capabilities = getattr(webdriver.DesiredCapabilities, self.browser_name.upper())
            if self.browser_version:
                capabilities['version'] = self.browser_version
            capabilities['platform'] = self.platform.upper()
            if self.capabilities:
                capabilities.update(json.loads(self.capabilities))
            executor = 'http://%s:%s/wd/hub' % (self.host, self.port)
            try:
                self.selenium = webdriver.Remote(command_executor=executor,
                                                 desired_capabilities=capabilities,
                                                 browser_profile=profile)
            except AttributeError:
                valid_browsers = [attr for attr in dir(webdriver.DesiredCapabilities) if not attr.startswith('__')]
                raise AttributeError("Invalid browser name: '%s'. Valid options are: %s" % (self.browser_name, ', '.join(valid_browsers)))

        elif self.driver.upper() == 'CHROME':
            if self.chrome_path:
                if self.chrome_options:
                    options = self.create_chrome_options(self.chrome_options)
                    self.selenium = webdriver.Chrome(executable_path=self.chrome_path,
                                                     chrome_options=options)
                else:
                    self.selenium = webdriver.Chrome(executable_path=self.chrome_path)
            else:
                if self.chrome_options:
                    options = self.create_chrome_options(self.chrome_options)
                    self.selenium = webdriver.Chrome(chrome_options=options)
                else:
                    self.selenium = webdriver.Chrome()

        elif self.driver.upper() == 'FIREFOX':
            binary = self.firefox_path and FirefoxBinary(self.firefox_path) or None
            self.selenium = webdriver.Firefox(
                firefox_binary=binary,
                firefox_profile=profile)
        elif self.driver.upper() == 'IE':
            self.selenium = webdriver.Ie()
        else:
            getattr(webdriver, self.driver)()

    def start_rc_client(self):
        self.selenium = selenium(self.host, str(self.port), self.browser, self.base_url)

        if self.capture_network:
            self.selenium.start('captureNetworkTraffic=true')
        else:
            self.selenium.start()

    @property
    def session_id(self):
        if self.webdriver:
            return self.selenium.session_id
        else:
            return self.selenium.get_eval('selenium.sessionId')

    def create_firefox_profile(self, preferences):
        profile = webdriver.FirefoxProfile()
        if preferences:
            [profile.set_preference(k, v) for k, v in json.loads(preferences).items()]
        profile.assume_untrusted_cert_issuer = self.assume_untrusted
        profile.update_preferences()
        return profile

    def create_chrome_options(self, preferences):
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

    @property
    def screenshot(self):
        try:
            if self.webdriver:
                screenshot = self.selenium.get_screenshot_as_base64()
            else:
                screenshot = self.selenium.capture_entire_page_screenshot_to_string('')
            return screenshot
        except:
            return None

    @property
    def html(self):
        try:
            if self.webdriver:
                html = self.selenium.page_source
            else:
                html = self.selenium.get_html_source()
            return html.encode('utf-8')
        except:
            return None

    @property
    def log(self):
        try:
            if self.rc:
                return self.selenium.get_log().encode('utf-8')
        except:
            return None

    @property
    def network_traffic(self):
        try:
            if self.rc and self.capture_network:
                return self.selenium.captureNetworkTraffic('json')
        except:
            return None

    @property
    def url(self):
        try:
            if self.webdriver:
                url = self.selenium.current_url
            else:
                url = self.selenium.get_location()
            return url
        except:
            return None

    def stop(self):
        try:
            if self.webdriver:
                self.selenium.quit()
            else:
                self.selenium.stop()
        except:
            pass
