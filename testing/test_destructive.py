#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testDestructiveTestsNotRunByDefault(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.skip_selenium
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port, file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 0


def testNonDestructiveTestsRunByDefault(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.skip_selenium
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port, file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testDestructiveTestsRunWhenForced(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.skip_selenium
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--destructive',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testBothDestructiveAndNonDestructiveTestsRunWhenForced(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.skip_selenium
        @pytest.mark.nondestructive
        def test_selenium1(mozwebqa):
            assert True
        @pytest.mark.skip_selenium
        def test_selenium2(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--destructive',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 2


def testSkipDestructiveTestsIfForcedAndRunningAgainstSensitiveURL(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.skip_selenium
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--sensitiveurl=localhost',
                                '--destructive',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(skipped) == 1
