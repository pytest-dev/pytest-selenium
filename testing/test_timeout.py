#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from webserver import SimpleWebServer

def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestTimeout.webserver = webserver

def teardown_module(module):
    TestTimeout.webserver.stop()

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
class TestTimeout:

    def testWebDriverWithDefaultTimeout(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_timeout(mozwebqa):
                assert mozwebqa.timeout == 60
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=webdriver', '--driver=firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1

    def testWebDriverWithCustomTimeout(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_timeout(mozwebqa):
                assert mozwebqa.timeout == 30
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=webdriver', '--driver=firefox', '--timeout=30', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1

    def testRCWithDefaultTimeout(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_timeout(mozwebqa):
                assert mozwebqa.timeout == 60000
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=*firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1

    def testRCWithCustomTimeout(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_timeout(mozwebqa):
                assert mozwebqa.timeout == 30000
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=*firefox', '--timeout=30', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
