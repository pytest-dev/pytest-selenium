#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testWebDriverWithDefaultTimeout(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_timeout(mozwebqa):
            assert mozwebqa.timeout == 60
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=webdriver',
                                '--driver=firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testWebDriverWithCustomTimeout(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_timeout(mozwebqa):
            assert mozwebqa.timeout == 30
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=webdriver',
                                '--driver=firefox',
                                '--timeout=30',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testRCWithDefaultTimeout(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_timeout(mozwebqa):
            assert mozwebqa.timeout == 60000
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=rc',
                                '--browser=*firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testRCWithCustomTimeout(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_timeout(mozwebqa):
            assert mozwebqa.timeout == 30000
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=rc',
                                '--browser=*firefox',
                                '--timeout=30',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
