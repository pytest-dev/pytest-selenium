#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from webserver import SimpleWebServer


def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestWebDriverClient.webserver = webserver


def teardown_module(module):
    TestWebDriverClient.webserver.stop()


@pytest.mark.skip_selenium
@pytest.mark.nondestructive
class TestWebDriverClient:

    def testStartWebDriverClient(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                mozwebqa.selenium.get('http://localhost:%s/')
                assert mozwebqa.selenium.find_element_by_tag_name('h1').text == 'Success!'
        """ % self.webserver.port)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=webdriver', '--driver=firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1
