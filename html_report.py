#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import cgi
import httplib
import json
import os
import py
import time


class HTMLReport(object):

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
        import pytest_mozwebqa
        (testclass, testmethod) = pytest_mozwebqa.split_class_and_test_names(report.nodeid)
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
        html.append('.log {display:inline-block; width:800px; max-height: 230px; overflow-y: scroll; color: black; border: 1px solid #E6E6E6; padding: 5px; background-color: #E6E6E6; font-family: "Courier New", Courier, monospace; white-space:pre-wrap}')
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
