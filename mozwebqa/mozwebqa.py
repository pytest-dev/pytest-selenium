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

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import selenium
from selenium import webdriver
import yaml


def pytest_configure(config):
    if config.option.base_url:
        status_code = _get_status_code(config.option.base_url)
        assert status_code == 200, 'Base URL did not return status code 200. (URL: %s, Response: %s)' % (config.option.base_url, status_code)

    report_path = config.option.webqa_report_path
    if report_path:
        config._html = LogHTML(report_path, config)
        config.pluginmanager.register(config._html)


def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


def pytest_runtest_setup(item):
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
    TestSetup.timeout = item.config.option.timeout
    TestSetup.default_implicit_wait = 10
    item.sauce_labs_credentials_file = item.config.option.sauce_labs_credentials_file

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
    if TestSetup.selenium and not 'skip_selenium' in item.keywords:
        _capture_debug(item)
        _stop_selenium(item)


def pytest_funcarg__mozwebqa(request):
    return TestSetup(request)


def pytest_addoption(parser):
    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--baseurl',
                     action='store',
                     dest='base_url',
                     metavar='url',
                     help='base url for the application under test.')
    group._addoption('--api',
                     action='store',
                     default='webdriver',
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
                     default=60000,
                     metavar='num',
                     help='timeout for page loads, etc (selenium rc).')
    group._addoption('--capturenetwork',
                     action='store_true',
                     dest='capture_network',
                     default=False,
                     help='capture network traffic to test_method_name.json (selenium rc). (disabled by default).')

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
                    default='results.html',
                    help="create mozilla webqa custom report file at given path. default is 'results.html'")


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
    if TestSetup.base_url is None:
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


def _start_selenium(item):
    if item.api == 'webdriver':
        _start_webdriver_client(item)
    else:
        _start_rc_client(item)


def _start_webdriver_client(item):
    if item.sauce_labs_credentials_file:
        capabilities = {
                    'platform': item.platform,
                    'browserName': item.browser_name,
                    'version': item.browser_version,
                    'name': ".".join(_split_class_and_test_names(item.nodeid)),
                    'tags': item.keywords.keys()[:-1],
                    'public': False}
        executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (item.sauce_labs_credentials['username'], item.sauce_labs_credentials['api-key'])
        TestSetup.selenium = webdriver.Remote(command_executor=executor,
                                              desired_capabilities=capabilities)
        _capture_session_id(item, _debug_path(item))
    else:
        if item.driver.upper() == 'REMOTE':
            capabilities = getattr(webdriver.DesiredCapabilities, item.browser_name.upper())
            capabilities['version'] = item.browser_version
            capabilities['platform'] = item.platform.upper()
            executor = 'http://%s:%s/wd/hub' % (item.host, item.port)
            try:
                TestSetup.selenium = webdriver.Remote(command_executor=executor,
                                                      desired_capabilities=capabilities)
            except AttributeError:
                valid_browsers = [attr for attr in dir(webdriver.DesiredCapabilities) if not attr.startswith('__')]
                raise AttributeError("Invalid browser name: '%s'. Valid options are: %s" % (item.browser_name, ', '.join(valid_browsers)))

        elif item.driver.upper() == 'CHROME':
            if hasattr(item, 'chrome_path'):
                TestSetup.selenium = webdriver.Chrome(executable_path=item.chrome_path)
            else:
                TestSetup.selenium = webdriver.Chrome()

        elif item.driver.upper() == 'FIREFOX':
            if hasattr(item, 'firefox_path'):
                TestSetup.selenium = webdriver.Firefox(firefox_binary=FirefoxBinary(item.firefox_path))
            else:
                TestSetup.selenium = webdriver.Firefox()

        elif item.driver.upper() == 'IE':
            TestSetup.selenium = webdriver.Ie()
        else:
            getattr(webdriver, item.driver)()

    TestSetup.selenium.implicitly_wait(TestSetup.default_implicit_wait)


def _start_rc_client(item):
    test_name = ".".join(_split_class_and_test_names(item.nodeid))
    if item.sauce_labs_credentials_file:
        TestSetup.selenium = selenium('ondemand.saucelabs.com', '80',
                                      json.dumps({
                                      'username': item.sauce_labs_credentials['username'],
                                      'access-key': item.sauce_labs_credentials['api-key'],
                                      'os': item.platform,
                                      'browser': item.browser_name,
                                      'browser-version': item.browser_version,
                                      'name': test_name,
                                      'tags': item.keywords.keys()[:-1],
                                      'public': False}),
                                      TestSetup.base_url)
    else:
        browser = item.environment or item.browser
        TestSetup.selenium = selenium(item.host, str(item.port), browser, TestSetup.base_url)

    if item.config.option.capture_network:
        TestSetup.selenium.start("captureNetworkTraffic=true")
    else:
        TestSetup.selenium.start()

    if item.sauce_labs_credentials_file:
        _capture_session_id(item, _debug_path(item))

    TestSetup.selenium.set_timeout(TestSetup.timeout)
    TestSetup.selenium.set_context(test_name)


def _debug_path(item):
    report_path = item.config.option.webqa_report_path
    debug_path = report_path and \
                 os.path.dirname(report_path) and \
                 os.path.sep.join([os.path.dirname(report_path), 'debug']) or 'debug'
    debug_path = os.path.normpath(os.path.expanduser(os.path.expandvars(debug_path)))
    if not os.path.exists(debug_path):
        os.makedirs(debug_path)
    return os.path.sep.join([debug_path, _generate_filename(*_split_class_and_test_names(item.nodeid))])


def _capture_debug(item):
    filename = _debug_path(item)
    _capture_screenshot(item, filename)
    _capture_html(item, filename)
    #_capture_log(item, filename)  # Log may contain passwords, etc so we shouldn't capture this until we can do so safely
    if item.config.option.capture_network:
        _capture_network(filename)


def _generate_filename(classname, testname):
    return '%s_%s' % (classname.replace('.', '_'), testname)


def _split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = tuple(names)
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def _capture_session_id(item, filename):
    f = open("%s.session" % filename, 'wb')
    if item.api.upper() == 'WEBDRIVER':
        f.write(TestSetup.selenium.session_id)
    else:
        f.write(TestSetup.selenium.get_eval('selenium.sessionId'))
    f.close()


def _capture_screenshot(item, filename):
    try:
        f = open("%s.png" % filename, 'wb')
        if item.api.upper() == 'WEBDRIVER':
            f.write(base64.decodestring(TestSetup.selenium.get_screenshot_as_base64()))
        else:
            f.write(base64.decodestring(TestSetup.selenium.capture_entire_page_screenshot_to_string('')))
        f.close()
    except:
        pass


def _capture_html(item, filename):
    f = open("%s.html" % filename, 'wb')
    if item.api.upper() == 'WEBDRIVER':
        f.write(TestSetup.selenium.page_source.encode('utf-8'))
    else:
        f.write(TestSetup.selenium.get_html_source().encode('utf-8'))
    f.close()


def _capture_log(item, filename):
    if item.api.upper() == 'RC':
        f = open("%s.log" % filename, 'wb')
        f.write(TestSetup.selenium.get_log().encode('utf-8'))
        f.close()


def _capture_network(filename):
    f = open('%s.json' % filename, 'w')
    f.write(TestSetup.selenium.captureNetworkTraffic('json'))
    f.close()


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

    def __init__(self, logfile, config):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(logfile)
        self.config = config
        self.test_logs = []
        self.errors = self.errors = 0
        self.passed = self.skipped = 0
        self.failed = self.failed = 0
        self.xfailed = self.xpassed = 0
        self._durations = {}

    def _appendrow(self, result, report):
        (classname, testname) = _split_class_and_test_names(report.nodeid)
        filename = os.path.sep.join(["debug", _generate_filename(classname, testname)])
        time = self._durations.pop(report.nodeid, 0.0)
        try:
            session_id = open('%s.session' % filename, 'r').readline()
        except:
            session_id = None
        links = {'HTML': '%s.html' % filename,
                 'Screenshot': '%s.png' % filename}
        if self.config.option.capture_network:
            links['Network'] = '%s.json' % filename
        if session_id:
            links['Sauce Labs Job'] = 'http://saucelabs.com/jobs/%s' % session_id
        # Log may contain passwords, etc so we shouldn't capture this until we can do so safely
        #if self.config.option.api.upper() == 'RC':
        #    links['Log'] = '%s.log' % filename
        links_html = []
        self.test_logs.append('\n<tr class="%s"><td class="%s">%s</td><td>%s</td><td>%s</td><td>%is</td>' % (result.lower(), result.lower(), result, classname, testname, round(time)))
        self.test_logs.append('<td>')
        for name, path in links.iteritems():
            links_html.append('<a href="%s">%s</a>' % (path, name))
        self.test_logs.append(', '.join(links_html))
        self.test_logs.append('</td>')

        if not 'Passed' in result:
            self.test_logs.append('\n<tr class="additional"><td colspan="5">')

            if report.longrepr:
                self.test_logs.append('\n<div class="log">')
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
                self.test_logs.append('\n</div>')

            self.test_logs.append('\n<div class="screenshot"><a href="%s"><img src="%s" /></a></div>' % (links['Screenshot'], links['Screenshot']))
            if session_id:
                self.test_logs.append('\n<div id="player%s" class="video">' % session_id)
                self.test_logs.append('\n<object width="100%" height="100%" type="application/x-shockwave-flash" data="http://saucelabs.com/flowplayer/flowplayer-3.2.5.swf?0.2566397726976729" name="player_api" id="player_api">')
                self.test_logs.append('\n<param value="true" name="allowfullscreen">')
                self.test_logs.append('\n<param value="always" name="allowscriptaccess">')
                self.test_logs.append('\n<param value="high" name="quality">')
                self.test_logs.append('\n<param value="true" name="cachebusting">')
                self.test_logs.append('\n<param value="#000000" name="bgcolor">')
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
                        &quot;autoBuffering&quot;:true}]}' % (session_id, session_id, session_id)
                self.test_logs.append('\n<param value="%s" name="flashvars">' % flash_vars.replace(' ', ''))
                self.test_logs.append('\n</object></div>')
            self.test_logs.append('\n</td></tr>')

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
        if report.passed:
            self.append_pass(report)
        elif report.failed:
            if report.when != "call":
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self.append_skipped(report)

    def pytest_runtest_call(self, item, __multicall__):
        start = time.time()
        try:
            return __multicall__.execute()
        finally:
            self._durations[item.nodeid] = time.time() - start

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus, __multicall__):
        logfile_dirname = os.path.dirname(self.logfile)
        if logfile_dirname and not os.path.exists(logfile_dirname):
            os.makedirs(logfile_dirname)
        logfile = py.std.codecs.open(self.logfile, 'w', encoding='utf-8')

        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed + self.xpassed + self.xfailed
        logfile.write('<html><head><title>Test Report</title><style>')
        logfile.write('\nbody {font-family: Helvetica, Arial, sans-serif; font-size: 12px}')
        logfile.write('\na {color: #999}')
        logfile.write('\nh2 {font-size: 16px}')
        logfile.write('\ntable {border: 1px solid #e6e6e6; color: #999; font-size: 12px; border-collapse: collapse}')
        logfile.write('\n#configuration tr:nth-child(odd) {background-color: #f6f6f6}')
        logfile.write('\nth, td {padding: 5px; border: 1px solid #E6E6E6; text-align: left}')
        logfile.write('\nth {font-weight: bold}')
        logfile.write('\ntr.passed, tr.skipped, tr.xfailed, tr.error, tr.failed, tr.xpassed {color: inherit}')
        logfile.write('\ntr.passed + tr.additional {display: none}')
        logfile.write('\n.passed {color: green}')
        logfile.write('\n.skipped, .xfailed {color: orange}')
        logfile.write('\n.error, .failed, .xpassed {color: red}')
        logfile.write('\n.log {display: inline-block; width: 800px; height: 230px; overflow-y: scroll; color: black; border: 1px solid #E6E6E6; padding: 5px; background-color: #E6E6E6; font-family: "Courier New", Courier, monospace; white-space: pre}')
        logfile.write('\n.screenshot {display: inline-block; border: 1px solid #E6E6E6; width: 320px; height: 240px; overflow: hidden}')
        logfile.write('\n.screenshot img {width: 320px}')
        logfile.write('\n.video {display: inline-block; width: 320px; height: 240px}')
        logfile.write('\n</style></head><body>')
        logfile.write('\n<h2>Configuration</h2>')
        logfile.write('\n<table id="configuration"><tr><th>Base URL</th><td><a href="%s">%s</td></tr>' % (self.config.option.base_url, self.config.option.base_url))
        logfile.write('\n<tr><th>Selenium API</th><td>%s</td></tr>' % self.config.option.api)
        if not self.config.option.driver.upper() == 'REMOTE':
            logfile.write('\n<tr><th>Driver</th><td>%s</td></tr>' % self.config.option.driver)
            if self.config.option.firefox_path:
                logfile.write('\n<tr><th>Firefox Path</th><td>%s</td></tr>' % self.config.option.firefox_path)
            elif self.config.option.chrome_path:
                logfile.write('\n<tr><th>Google Chrome Path</th><td>%s</td></tr>' % self.config.option.chrome_path)
        else:
            selenium_server = self.config.option.sauce_labs_credentials_file and 'Sauce Labs' or 'http://%s:%s' % (self.config.option.host, self.config.option.port)
            logfile.write('\n<tr><th>Selenium Server</th><td>%s</td></tr>' % selenium_server)
            if self.config.option.api.upper() == 'WEBDRIVER' or self.config.option.sauce_labs_credentials_file:
                logfile.write('\n<tr><th>Browser</th><td>%s %s on %s</td></tr>' % (self.config.option.browser_name.title(), self.config.option.browser_version, self.config.option.platform.title()))
            else:
                logfile.write('\n<tr><th>Browser</th><td>%s</td></tr>' % self.config.option.environment or self.config.option.browser)
            if self.config.option.api.upper() == 'RC':
                logfile.write('\n<tr><th>Timeout</th><td>%s</td></tr>' % self.config.option.timeout)
        logfile.write('\n<tr><th>Capture Network Traffic</th><td>%s</td></tr>' % self.config.option.capture_network)
        if self.config.option.credentials_file:
            logfile.write('\n<tr><th>Credentials</th><td>%s</td></tr>' % self.config.option.credentials_file)
        if self.config.option.sauce_labs_credentials_file:
            logfile.write('\n<tr><th>Sauce Labs Credentials</th><td>%s</td></tr>' % self.config.option.sauce_labs_credentials_file)
        logfile.write('\n</table>')
        logfile.write('\n<h2>Summary</h2>')
        logfile.write('\n<p>%i tests ran in %i seconds.<br />' % (numtests, suite_time_delta))
        logfile.write('\n<span class="passed">%i passed</span>, ' % self.passed)
        logfile.write('<span class="skipped">%i skipped</span>, ' % self.skipped)
        logfile.write('<span class="failed">%i failed</span>, ' % self.failed)
        logfile.write('<span class="error">%i errors</span>.<br />' % self.errors)
        logfile.write('\n<span class="skipped">%i expected failures</span>, ' % self.xfailed)
        logfile.write('<span class="failed">%i unexpected passes</span>.</p>' % self.xpassed)
        logfile.write('\n<h2>Results</h2>')
        logfile.write('\n<table id="results">')
        logfile.write('\n<tr><th>Result</th><th>Class</th><th>Name</th><th>Duration</th><th>Links</th></tr>')
        logfile.writelines(self.test_logs)
        logfile.write('\n</table></body></html>')
        logfile.close()


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
