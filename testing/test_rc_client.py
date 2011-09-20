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
import pytest
import json

from webserver import SimpleWebServer


def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestRCClient.webserver = webserver


def teardown_module(module):
    TestRCClient.webserver.stop()


@pytest.mark.skip_selenium
class TestRCClient:

    def testStartRCClientUsingEnvironment(self, testdir):
        file_test = testdir.makepyfile("""
            def test_selenium(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--environment=Firefox Beta on Mac OS X', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1

    def testStartRCClientUsingBrowser(self, testdir):
        file_test = testdir.makepyfile("""
            def test_selenium(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1

    def testStartRCClientAndCaptureNetworkTraffic(self, testdir):
        file_test = testdir.makepyfile("""
            def test_capture_network_traffic(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--capturenetwork', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
        filename = os.path.sep.join([str(testdir.tmpdir), 'test_capture_network_traffic.json'])
        json_data = open(filename)
        data = json.load(json_data)
        json_data.close()
        assert len(data) > 0
