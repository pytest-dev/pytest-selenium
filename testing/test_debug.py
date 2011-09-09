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

from webserver import SimpleWebServer

def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestDebug.webserver = webserver

def teardown_module(module):
    TestDebug.webserver.stop()

@pytest.mark.skip_selenium
class TestDebug:

    def testDebugWithoutReportSubdirectory(self, testdir):
        file_test = testdir.makepyfile("""
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=result.html', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
        debug_path = os.path.sep.join([str(testdir.tmpdir), 'debug'])
        for file_extension in ['png', 'html']:
            debug_file = os.path.sep.join([debug_path, [filename for filename in os.listdir(debug_path) if filename.endswith('test_debug.%s' % file_extension)][0]])
            assert os.path.exists(debug_file)
            assert os.path.isfile(debug_file)

    def testDebugWithReportSubdirectory(self, testdir):
        file_test = testdir.makepyfile("""
            def test_debug(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        report_subdirectory = 'report'
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=Firefox Beta on Mac OS X', '--webqareport=%s/result.html' % report_subdirectory, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
        debug_path = os.path.sep.join([str(testdir.tmpdir), report_subdirectory, 'debug'])
        for file_extension in ['png', 'html']:
            debug_file = os.path.sep.join([debug_path, [filename for filename in os.listdir(debug_path) if filename.endswith('test_debug.%s' % file_extension)][0]])
            assert os.path.exists(debug_file)
            assert os.path.isfile(debug_file)
