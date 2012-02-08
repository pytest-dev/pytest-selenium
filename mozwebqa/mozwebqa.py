#!/usr/bin/env python
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla WebQA Tests.
#
# The Initial Developer of the Original Code is Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s): Dave Hunt <dhunt@mozilla.com>
#                 David Burns
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import cgi
import base64
import json
import os
import pytest
import py
import time
import urllib2
import httplib
import ConfigParser

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import selenium
from selenium import webdriver
import yaml


def pytest_configure(config):
    if not hasattr(config, 'slaveinput'):

        if config.option.base_url:
            status_code = _get_status_code(config.option.base_url)
            assert status_code == 200, 'Base URL did not return status code 200. (URL: %s, Response: %s)' % (config.option.base_url, status_code)

        if config.option.webqa_report_path:
            config._html = LogHTML(config)
            config.pluginmanager.register(config._html)


def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


def pytest_runtest_setup(item):
    item.debug = _create_debug()
    item.api = item.config.option.api
    item.host = item.config.option.host
    item.port = item.config.option.port
    item.driver = item.config.option.driver
    item.chrome_path = item.config.option.chrome_path
    item.firefox_path = item.config.option.firefox_path
    item.browser = item.config.option.browser
    item.environment = item.config.option.environment
    item.browser_name = item.config.option.browser_name
    item.browser_version = item.config.option.browser_version
    item.platform = item.config.option.platform
    TestSetup.base_url = item.config.option.base_url
    TestSetup.default_implicit_wait = 10
    item.sauce_labs_credentials_file = item.config.option.sauce_labs_credentials_file

    if item.config.option.api.upper() == 'RC':
        TestSetup.timeout = item.config.option.timeout * 1000
    else:
        TestSetup.timeout = item.config.option.timeout

    if item.sauce_labs_credentials_file:
        item.sauce_labs_credentials = _credentials(item.config.option.sauce_labs_credentials_file)

    item.credentials_file = item.config.option.credentials_file

    if item.credentials_file:
        TestSetup.credentials = _credentials(item.credentials_file)

    if not 'skip_selenium' in item.keywords:
        _check_selenium_usage(item)
        _start_selenium(item)
    else:
        TestSetup.selenium = None


def pytest_runtest_teardown(item):
    if hasattr(TestSetup, 'selenium') and TestSetup.selenium and not 'skip_selenium' in item.keywords:
        _stop_selenium(item)


def pytest_runtest_makereport(__multicall__, item, call):
    report = __multicall__.execute()
    if report.when == 'call':
        report.session_id = getattr(item, 'session_id', None)
        if hasattr(TestSetup, 'selenium') and TestSetup.selenium and not 'skip_selenium' in item.keywords:
            if report.skipped and 'xfail' in report.keywords or report.failed and 'xfail' not in report.keywords:
                _capture_url(item)
                _capture_screenshot(item)
                _capture_html(item)
                _capture_log(item)
                report.sections.append(('pytest-mozwebqa', _debug_summary(item.debug)))
            _capture_network_traffic(item)
            report.debug = item.debug
    return report


def pytest_funcarg__mozwebqa(request):
    return TestSetup(request)


def pytest_addoption(parser):
    config = ConfigParser.ConfigParser(defaults={
        'baseurl': '',
        'api': 'webdriver'
    })
    config.read('mozwebqa.cfg')

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--baseurl',
                     action='store',
                     dest='base_url',
                     default=config.get('DEFAULT', 'baseurl'),
                     metavar='url',
                     help='base url for the application under test.')
    group._addoption('--api',
                     action='store',
                     default=config.get('DEFAULT', 'api'),
                     metavar='api',
                     help="version of selenium api to use. 'rc' uses selenium rc. 'webdriver' uses selenium webdriver (the default).")
    group._addoption('--host',
                     action='store',
                     default='localhost',
                     metavar='str',
                     help='host that selenium server is listening on.')
    group._addoption('--port',
                     action='store',
                     type='int',
                     default=4444,
                     metavar='num',
                     help='port that selenium server is listening on.')
    group._addoption('--driver',
                     action='store',
                     dest='driver',
                     default='Remote',
                     metavar='str',
                     help='webdriver implementation.')
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
                     action='store',
                     dest='firefox_preferences',
                     metavar='str',
                     help='json string of firefox preferences to set (webdriver).')
    group._addoption('--chromeopts',
                     action='store',
                     dest='chrome_options',
                     metavar='str',
                     help='json string of google chrome options to set (webdriver).')
    group._addoption('--browser',
                     action='store',
                     dest='browser',
                     metavar='str',
                     help='target browser (standalone rc server).')
    group._addoption('--environment',
                     action='store',
                     dest='environment',
                     metavar='str',
                     help='target environment (grid rc).')
    group._addoption('--browsername',
                     action='store',
                     dest='browser_name',
                     metavar='str',
                     help='target browser name (webdriver).')
    group._addoption('--browserver',
                     action='store',
                     dest='browser_version',
                     metavar='str',
                     help='target browser version (webdriver).')
    group._addoption('--platform',
                     action='store',
                     metavar='str',
                     help='target platform (webdriver).')
    group._addoption('--timeout',
                     action='store',
                     type='int',
                     default=60,
                     metavar='num',
                     help='timeout (in seconds) for page loads, etc.')
    group._addoption('--capturenetwork',
                     action='store_true',
                     dest='capture_network',
                     default=False,
                     help='capture network traffic to test_method_name.json (selenium rc). (disabled by default).')
    group._addoption('--build',
                     action='store',
                     dest='build',
                     metavar='str',
                     help='build identifier (for continuous integration).')

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--credentials",
                     action="store",
                     dest='credentials_file',
                     metavar='path',
                     help="location of yaml file containing user credentials.")
    group._addoption('--saucelabs',
                     action='store',
                     dest='sauce_labs_credentials_file',
                     metavar='path',
                     help='credendials file containing sauce labs username and api key.')

    group = parser.getgroup("terminal reporting")
    group.addoption('--webqareport',
                    action='store',
                    dest='webqa_report_path',
                    metavar='path',
                    default='results/index.html',
                    help="create mozilla webqa custom report file at given path. default is 'results/index.html'")


def _get_status_code(url):
    try:
        connection = urllib2.urlopen(url)
        status_code = connection.getcode()
        connection.close()
        return status_code
    except urllib2.HTTPError, e:
        return e.getcode()
    except urllib2.URLError, e:
        print 'Unable to connect to: %s' % url


def _create_debug():
    return {
        'urls': [],
        'screenshots': [],
        'html': [],
        'logs': [],
        'network_traffic': []}


def _debug_summary(debug):
    summary = []
    if debug['urls']:
        summary.append('Failing URL: %s' % debug['urls'][-1])
    return '\n'.join(summary)


def _credentials(credentials_file):
    stream = file(credentials_file, 'r')
    credentials = yaml.load(stream)
    return credentials


def _check_sauce_usage(item):
    '''
        If this is for Sauce Labs usage, we need to check a few details
    '''
    if not item.sauce_labs_credentials['username']:
        raise pytest.UsageError('username must be specified in the sauce labs credentials file.')

    if not item.sauce_labs_credentials['api-key']:
        raise pytest.UsageError('api-key must be specified in the sauce labs credentials file.')

    if item.api == "rc":
        if not item.browser_name:
            raise pytest.UsageError("--browsername must be specified when using the 'rc' api with sauce labs.")

        if not item.browser_version:
            raise pytest.UsageError("--browserver must be specified when using the 'rc' api with sauce labs.")

        if not item.platform:
            raise pytest.UsageError("--platform must be specified when using the 'rc' api with sauce labs.")


def _check_selenium_usage(item):
    '''
        Check that the usage parameters are correct. If wrong throws the appropriate error
    '''
    if not TestSetup.base_url:
        raise pytest.UsageError('--baseurl must be specified.')

    if item.sauce_labs_credentials_file:
        _check_sauce_usage(item)

    if item.api == 'webdriver':
        if item.driver.upper() == 'REMOTE':
            if not item.browser_name:
                raise pytest.UsageError("--browsername must be specified when using the 'webdriver' api.")

            if not item.browser_version:
                raise pytest.UsageError("--browserver must be specified when using the 'webdriver' api.")

            if not item.platform:
                raise pytest.UsageError("--platform must be specified when using the 'webdriver' api.")
    else:
        if not item.sauce_labs_credentials_file and not(item.browser or item.environment):
            raise pytest.UsageError("--browser or --environment must be specified when using the 'rc' api.")


def _get_common_sauce_settings(item):
    config = ConfigParser.ConfigParser(defaults={'tags': ''})
    config.read('mozwebqa.cfg')
    tags = config.get('DEFAULT', 'tags').split(',')
    tags.extend([mark for mark in item.keywords.keys() if not mark.startswith('test')])
    return {'build': item.config.option.build or None,
            'name': '.'.join(_split_class_and_test_names(item.nodeid)),
            'tags': tags,
            'public': 'private' not in item.keywords,
            'restricted-public-info': 'public' not in item.keywords}


def _create_firefox_profile(preferences):
    if preferences:
        profile = webdriver.FirefoxProfile()
        for key, value in json.loads(preferences).items():
            if isinstance(value, unicode):
                value = str(value)
            profile.set_preference(key, value)
        profile.update_preferences()
        return profile
    else:
        return None


def _create_chrome_options(preferences):
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


def _start_selenium(item):
    if item.api == 'webdriver':
        _start_webdriver_client(item)
    else:
        _start_rc_client(item)
    _capture_session_id(item)


def _start_webdriver_client(item):
    if item.sauce_labs_credentials_file:
        capabilities = _get_common_sauce_settings(item)
        capabilities.update({'platform': item.platform,
                         'browserName': item.browser_name,
                         'version': item.browser_version})
        executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (item.sauce_labs_credentials['username'], item.sauce_labs_credentials['api-key'])
        TestSetup.selenium = webdriver.Remote(command_executor=executor,
                                              desired_capabilities=capabilities)
    else:
        profile = _create_firefox_profile(item.config.option.firefox_preferences)
        if item.driver.upper() == 'REMOTE':
            if item.config.option.chrome_options:
                capabilities = _create_chrome_options(item.config.option.chrome_options).to_capabilities()
            else:
                capabilities = getattr(webdriver.DesiredCapabilities, item.browser_name.upper())
            capabilities['version'] = item.browser_version
            capabilities['platform'] = item.platform.upper()
            executor = 'http://%s:%s/wd/hub' % (item.host, item.port)
            try:
                TestSetup.selenium = webdriver.Remote(command_executor=executor,
                                                      desired_capabilities=capabilities,
                                                      browser_profile=profile)
            except AttributeError:
                valid_browsers = [attr for attr in dir(webdriver.DesiredCapabilities) if not attr.startswith('__')]
                raise AttributeError("Invalid browser name: '%s'. Valid options are: %s" % (item.browser_name, ', '.join(valid_browsers)))

        elif item.driver.upper() == 'CHROME':
            if item.config.option.chrome_path:
                if item.config.option.chrome_options:
                    options = _create_chrome_options(item.config.option.chrome_options)
                    TestSetup.selenium = webdriver.Chrome(executable_path=item.chrome_path,
                                                          chrome_options=options)
                else:
                    TestSetup.selenium = webdriver.Chrome(executable_path=item.chrome_path)
            else:
                if item.config.option.chrome_options:
                    options = _create_chrome_options(item.config.option.chrome_options)
                    TestSetup.selenium = webdriver.Chrome(chrome_options=options)
                else:
                    TestSetup.selenium = webdriver.Chrome()

        elif item.driver.upper() == 'FIREFOX':
            binary = hasattr(item, 'firefox_path') and FirefoxBinary(item.firefox_path) or None
            TestSetup.selenium = webdriver.Firefox(
                firefox_binary=binary,
                firefox_profile=profile)
        elif item.driver.upper() == 'IE':
            TestSetup.selenium = webdriver.Ie()
        else:
            getattr(webdriver, item.driver)()

    TestSetup.selenium.implicitly_wait(TestSetup.default_implicit_wait)


def _start_rc_client(item):
    if item.sauce_labs_credentials_file:
        settings = _get_common_sauce_settings(item)
        settings.update({'username': item.sauce_labs_credentials['username'],
                         'access-key': item.sauce_labs_credentials['api-key'],
                         'os': item.platform,
                         'browser': item.browser_name,
                         'browser-version': item.browser_version})
        TestSetup.selenium = selenium('ondemand.saucelabs.com', '80',
                                      json.dumps(settings),
                                      TestSetup.base_url)
    else:
        browser = item.environment or item.browser
        TestSetup.selenium = selenium(item.host, str(item.port), browser, TestSetup.base_url)

    if item.config.option.capture_network:
        TestSetup.selenium.start("captureNetworkTraffic=true")
    else:
        TestSetup.selenium.start()

    TestSetup.selenium.set_timeout(TestSetup.timeout)
    TestSetup.selenium.set_context(".".join(_split_class_and_test_names(item.nodeid)))


def _split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = tuple(names)
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def _capture_session_id(item):
    if item.api.upper() == 'WEBDRIVER':
        session_id = TestSetup.selenium.session_id
    else:
        session_id = TestSetup.selenium.get_eval('selenium.sessionId')
    item.session_id = session_id


def _capture_screenshot(item):
    if item.api.upper() == 'WEBDRIVER':
        screenshot = TestSetup.selenium.get_screenshot_as_base64()
    else:
        screenshot = TestSetup.selenium.capture_entire_page_screenshot_to_string('')
    item.debug['screenshots'].append(screenshot)


def _capture_html(item):
    if item.api.upper() == 'WEBDRIVER':
        html = TestSetup.selenium.page_source.encode('utf-8')
    else:
        html = TestSetup.selenium.get_html_source().encode('utf-8')
    item.debug['html'].append(html)


def _capture_log(item):
    if item.api.upper() == 'RC':
        log = TestSetup.selenium.get_log().encode('utf-8')
        item.debug['logs'].append(log)


def _capture_network_traffic(item):
    if item.api.upper() == 'RC' and item.config.option.capture_network:
        network_traffic = TestSetup.selenium.captureNetworkTraffic('json')
        item.debug['network_traffic'].append(network_traffic)


def _capture_url(item):
    if item.api.upper() == 'WEBDRIVER':
        url = TestSetup.selenium.current_url
    else:
        url = TestSetup.selenium.get_location()
    item.debug['urls'].append(url)


def _stop_selenium(item):
    if item.api == 'webdriver':
        try:
            TestSetup.selenium.quit()
        except:
            pass
    else:
        try:
            TestSetup.selenium.stop()
        except:
            pass


class LogHTML(object):

    def __init__(self, config):
        logfile = os.path.expanduser(os.path.expandvars(config.option.webqa_report_path))
        self.logfile = os.path.normpath(logfile)
        self._debug_path = 'debug'
        self.config = config
        self.test_logs = []
        self.errors = self.errors = 0
        self.passed = self.skipped = 0
        self.failed = self.failed = 0
        self.xfailed = self.xpassed = 0

    def _debug_paths(self, testclass, testmethod):
        root_path = os.path.join(os.path.dirname(self.logfile), self._debug_path)
        root_path = os.path.normpath(os.path.expanduser(os.path.expandvars(root_path)))
        test_path = os.path.join(testclass.replace('.', '_'), testmethod)
        full_path = os.path.join(root_path, test_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        relative_path = os.path.join(self._debug_path, test_path)
        absolute_path = os.path.join(root_path, test_path)
        return (relative_path, full_path)

    def _appendrow(self, result, report):
        (testclass, testmethod) = _split_class_and_test_names(report.nodeid)
        time = getattr(report, 'duration', 0.0)

        links = {}
        if hasattr(report, 'debug') and any(report.debug.values()):
            (relative_path, full_path) = self._debug_paths(testclass, testmethod)

            if report.debug['screenshots']:
                filename = 'screenshot.png'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(base64.decodestring(report.debug['screenshots'][-1]))
                links.update({'Screenshot': os.path.join(relative_path, filename)})

            if report.debug['html']:
                filename = 'html.txt'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(report.debug['html'][-1])
                links.update({'HTML': os.path.join(relative_path, filename)})

            # Log may contain passwords, etc so we only capture it for tests marked as public
            if report.debug['logs'] and 'public' in report.keywords:
                filename = 'log.txt'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(report.debug['logs'][-1])
                links.update({'Log': os.path.join(relative_path, filename)})

            if report.debug['network_traffic']:
                filename = 'networktraffic.json'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(report.debug['network_traffic'][-1])
                links.update({'Network Traffic': os.path.join(relative_path, filename)})

            if report.debug['urls']:
                links.update({'Failing URL': report.debug['urls'][-1]})

        if self.config.option.sauce_labs_credentials_file and hasattr(report, 'session_id'):
            links['Sauce Labs Job'] = 'http://saucelabs.com/jobs/%s' % report.session_id

        links_html = []
        self.test_logs.append('<tr class="%s"><td class="%s">%s</td><td>%s</td><td>%s</td><td>%is</td>' % (result.lower(), result.lower(), result, testclass, testmethod, round(time)))
        self.test_logs.append('<td>')
        for name, path in links.iteritems():
            links_html.append('<a href="%s">%s</a>' % (path, name))
        self.test_logs.append(', '.join(links_html))
        self.test_logs.append('</td>')

        if not 'Passed' in result:
            self.test_logs.append('<tr class="additional"><td colspan="5">')

            if report.longrepr:
                self.test_logs.append('<div class="log">')
                for line in str(report.longrepr).splitlines():
                    separator = line.startswith('_ ' * 10)
                    if separator:
                        self.test_logs.append(line[:80])
                    else:
                        exception = line.startswith("E   ")
                        if exception:
                            self.test_logs.append('<span class="error">%s</span>' % cgi.escape(line))
                        else:
                            self.test_logs.append(cgi.escape(line))
                    self.test_logs.append('<br />')
                self.test_logs.append('</div>')

            if 'Screenshot' in links:
                self.test_logs.append('<div class="screenshot"><a href="%s"><img src="%s" /></a></div>' % (links['Screenshot'], links['Screenshot']))

            if self.config.option.sauce_labs_credentials_file and hasattr(report, 'session_id'):
                self.test_logs.append('<div id="player%s" class="video">' % report.session_id)
                self.test_logs.append('<object width="100%" height="100%" type="application/x-shockwave-flash" data="http://saucelabs.com/flowplayer/flowplayer-3.2.5.swf?0.2566397726976729" name="player_api" id="player_api">')
                self.test_logs.append('<param value="true" name="allowfullscreen">')
                self.test_logs.append('<param value="always" name="allowscriptaccess">')
                self.test_logs.append('<param value="high" name="quality">')
                self.test_logs.append('<param value="true" name="cachebusting">')
                self.test_logs.append('<param value="#000000" name="bgcolor">')
                flash_vars = 'config={\
                    &quot;clip&quot;:{\
                        &quot;url&quot;:&quot;http%%3A//saucelabs.com/jobs/%s/video.flv&quot;,\
                        &quot;provider&quot;:&quot;streamer&quot;,\
                        &quot;autoPlay&quot;:false,\
                        &quot;autoBuffering&quot;:true},\
                    &quot;plugins&quot;:{\
                        &quot;streamer&quot;:{\
                            &quot;url&quot;:&quot;http://saucelabs.com/flowplayer/flowplayer.pseudostreaming-3.2.5.swf&quot;},\
                        &quot;controls&quot;:{\
                            &quot;mute&quot;:false,\
                            &quot;volume&quot;:false,\
                            &quot;backgroundColor&quot;:&quot;rgba(0, 0, 0, 0.7)&quot;}},\
                    &quot;playerId&quot;:&quot;player%s&quot;,\
                    &quot;playlist&quot;:[{\
                        &quot;url&quot;:&quot;http%%3A//saucelabs.com/jobs/%s/video.flv&quot;,\
                        &quot;provider&quot;:&quot;streamer&quot;,\
                        &quot;autoPlay&quot;:false,\
                        &quot;autoBuffering&quot;:true}]}' % (report.session_id, report.session_id, report.session_id)
                self.test_logs.append('<param value="%s" name="flashvars">' % flash_vars.replace(' ', ''))
                self.test_logs.append('</object></div>')
            self.test_logs.append('</td></tr>')

    def _make_report_dir(self):
        logfile_dirname = os.path.dirname(self.logfile)
        if logfile_dirname and not os.path.exists(logfile_dirname):
            os.makedirs(logfile_dirname)
        return logfile_dirname

    def _send_result_to_sauce(self, report):
        if hasattr(report, 'session_id'):
            try:
                result = {'passed': report.passed or (report.failed and 'xfail' in report.keywords)}
                credentials = _credentials(self.config.option.sauce_labs_credentials_file)
                basic_authentication = ('%s:%s' % (credentials['username'], credentials['api-key'])).encode('base64')[:-1]
                connection = httplib.HTTPConnection('saucelabs.com')
                connection.request('PUT', '/rest/v1/%s/jobs/%s' % (credentials['username'], report.session_id),
                                   json.dumps(result),
                                   headers={'Authorization': 'Basic %s' % basic_authentication,
                                            'Content-Type': 'text/json'})
                connection.getresponse()
            except:
                pass

    def append_pass(self, report):
        self.passed += 1
        self._appendrow('Passed', report)

    def append_failure(self, report):
        if "xfail" in report.keywords:
            self._appendrow('XPassed', report)
            self.xpassed += 1
        else:
            self._appendrow('Failed', report)
            self.failed += 1

    def append_error(self, report):
        self._appendrow('Error', report)
        self.errors += 1

    def append_skipped(self, report):
        if "xfail" in report.keywords:
            self._appendrow('XFailed', report)
            self.xfailed += 1
        else:
            self._appendrow('Skipped', report)
            self.skipped += 1

    def pytest_runtest_logreport(self, report):
        if self.config.option.sauce_labs_credentials_file:
            self._send_result_to_sauce(report)

        if report.passed:
            if report.when == 'call':
                self.append_pass(report)
        elif report.failed:
            if report.when != "call":
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self.append_skipped(report)

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus, __multicall__):
        self._make_report_dir()
        logfile = py.std.codecs.open(self.logfile, 'w', encoding='utf-8')

        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed + self.xpassed + self.xfailed

        server = self.config.option.sauce_labs_credentials_file and \
                 'Sauce Labs' or 'http://%s:%s' % (self.config.option.host, self.config.option.port)
        browser = self.config.option.browser_name and \
                  self.config.option.browser_version and \
                  self.config.option.platform and \
                  '%s %s on %s' % (str(self.config.option.browser_name).title(),
                                   self.config.option.browser_version,
                                   str(self.config.option.platform).title()) or \
                  self.config.option.environment or \
                  self.config.option.browser

        configuration = {
            'Base URL': self.config.option.base_url,
            'Build': self.config.option.build,
            'Selenium API': self.config.option.api,
            'Driver': self.config.option.driver,
            'Firefox Path': self.config.option.firefox_path,
            'Google Chrome Path': self.config.option.chrome_path,
            'Selenium Server': server,
            'Browser': browser,
            'Timeout': self.config.option.timeout,
            'Capture Network Traffic': self.config.option.capture_network,
            'Credentials': self.config.option.credentials_file,
            'Sauce Labs Credentials': self.config.option.sauce_labs_credentials_file}

        html = []
        html.append('<html><head><title>Test Report</title><style>')
        html.append('body {font-family: Helvetica, Arial, sans-serif; font-size: 12px}')
        html.append('a {color: #999}')
        html.append('h2 {font-size: 16px}')
        html.append('table {border: 1px solid #e6e6e6; color: #999; font-size: 12px; border-collapse: collapse}')
        html.append('#configuration tr:nth-child(odd) {background-color: #f6f6f6}')
        html.append('th, td {padding: 5px; border: 1px solid #E6E6E6; text-align: left}')
        html.append('th {font-weight: bold}')
        html.append('tr.passed, tr.skipped, tr.xfailed, tr.error, tr.failed, tr.xpassed {color: inherit}')
        html.append('tr.passed + tr.additional {display: none}')
        html.append('.passed {color: green}')
        html.append('.skipped, .xfailed {color: orange}')
        html.append('.error, .failed, .xpassed {color: red}')
        html.append('.log {display: inline-block; width: 800px; height: 230px; overflow-y: scroll; color: black; border: 1px solid #E6E6E6; padding: 5px; background-color: #E6E6E6; font-family: "Courier New", Courier, monospace; white-space: pre}')
        html.append('.screenshot {display: inline-block; border: 1px solid #E6E6E6; width: 320px; height: 240px; overflow: hidden}')
        html.append('.screenshot img {width: 320px}')
        html.append('.video {display: inline-block; width: 320px; height: 240px}')
        html.append('</style></head><body>')
        html.append('<h2>Configuration</h2>')
        html.append('<table id="configuration">')
        html.append('\n'.join(['<tr><td>%s</td><td>%s</td></tr>' % (k, v) for k, v in sorted(configuration.items()) if v]))
        html.append('</table>')
        html.append('<h2>Summary</h2>')
        html.append('<p>%i tests ran in %i seconds.<br />' % (numtests, suite_time_delta))
        html.append('<span class="passed">%i passed</span>, ' % self.passed)
        html.append('<span class="skipped">%i skipped</span>, ' % self.skipped)
        html.append('<span class="failed">%i failed</span>, ' % self.failed)
        html.append('<span class="error">%i errors</span>.<br />' % self.errors)
        html.append('<span class="skipped">%i expected failures</span>, ' % self.xfailed)
        html.append('<span class="failed">%i unexpected passes</span>.</p>' % self.xpassed)
        html.append('<h2>Results</h2>')
        html.append('<table id="results">')
        html.append('<tr><th>Result</th><th>Class</th><th>Name</th><th>Duration</th><th>Links</th></tr>')
        html.append(''.join(self.test_logs))
        html.append('</table></body></html>')
        logfile.write('\n'.join(html))
        logfile.close()


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
