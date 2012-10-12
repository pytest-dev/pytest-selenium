#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testStartRCClientUsingEnvironment(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--environment=*firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testStartRCClientUsingBrowser(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
