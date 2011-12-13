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

import os
import json
import pytest

from webserver import SimpleWebServer

def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestDebug.webserver = webserver

def teardown_module(module):
    TestDebug.webserver.stop()

@pytest.mark.skip_selenium
class TestDebug:

    failure_files = ('screenshot.png', 'html.txt')
    log_file = 'log.txt'
    network_traffic_file = 'networktraffic.json'

    def testDebugOnFail(self, testdir):
        file_test = testdir.makepyfile("""
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        path = self._test_debug_path(str(testdir.tmpdir))
        for file in self.failure_files:
            assert os.path.exists(os.path.join(path, file))
            assert os.path.isfile(os.path.join(path, file))

    def testDebugOnXFail(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.xfail
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(skipped) == 1
        path = self._test_debug_path(str(testdir.tmpdir))
        for file in self.failure_files:
            assert os.path.exists(os.path.join(path, file))
            assert os.path.isfile(os.path.join(path, file))

    def testNoDebugOnPass(self, testdir):
        file_test = testdir.makepyfile("""
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
        debug_path = os.path.sep.join([str(testdir.tmpdir), 'debug'])
        assert not os.path.exists(debug_path)

    def testNoDebugOnXPass(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.xfail
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        debug_path = os.path.sep.join([str(testdir.tmpdir), 'debug'])
        assert not os.path.exists(debug_path)

    def testNoDebugOnSkip(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.skipif('True')
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(skipped) == 1
        debug_path = os.path.sep.join([str(testdir.tmpdir), 'debug'])
        assert not os.path.exists(debug_path)

    def testDebugWithReportSubdirectory(self, testdir):
        file_test = testdir.makepyfile("""
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
        """)
        report_subdirectory = 'report'
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=%s/result.html' % report_subdirectory, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        path = self._test_debug_path(os.path.join(str(testdir.tmpdir), report_subdirectory))
        for file in self.failure_files:
            assert os.path.exists(os.path.join(path, file))
            assert os.path.isfile(os.path.join(path, file))

    def testLogWhenPublic(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.public
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        path = self._test_debug_path(str(testdir.tmpdir))
        assert os.path.exists(os.path.join(path, self.log_file))
        assert os.path.isfile(os.path.join(path, self.log_file))

    def testNoLogWhenNotPublic(self, testdir):
        file_test = testdir.makepyfile("""
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        path = self._test_debug_path(str(testdir.tmpdir))
        assert not os.path.exists(os.path.join(path, self.log_file))

    def testNoLogWhenPrivate(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.private
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') != 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        path = self._test_debug_path(str(testdir.tmpdir))
        assert not os.path.exists(os.path.join(path, self.log_file))

    def testCaptureNetworkTraffic(self, testdir):
        file_test = testdir.makepyfile("""
            def test_capture_network_traffic(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--capturenetwork', '--webqareport=index.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
        path = self._test_debug_path(str(testdir.tmpdir))
        json_data = open(os.path.join(path, self.network_traffic_file))
        data = json.load(json_data)
        json_data.close()
        assert len(data) > 0

    def _test_debug_path(self, root_path):
        debug_path = os.path.join(root_path, 'debug')
        for i in range(2):
            debug_path = os.path.join(debug_path, os.listdir(debug_path)[0])
        return debug_path
