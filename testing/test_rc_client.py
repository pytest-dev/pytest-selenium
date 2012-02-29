#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
@pytest.mark.nondestructive
class TestRCClient:

    def testStartRCClientUsingEnvironment(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=*firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1

    def testStartRCClientUsingBrowser(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                mozwebqa.selenium.open('/')
                assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--browser=*firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
