# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


def test_skip_destructive_by_default(testdir):
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa(file_test, passed=0, failed=0, skipped=0)


def test_run_non_destructive_by_default(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(): pass
    """)
    testdir.quick_qa(file_test, passed=1)


def test_run_destructive_when_forced(testdir):
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa('--destructive', file_test, passed=1)


def test_run_destructive_and_non_destructive_when_forced(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass1(): pass
        def test_pass2(): pass
    """)
    testdir.quick_qa('--destructive', file_test, passed=2)


def test_skip_destructive_when_forced_and_sensitive(testdir):
    file_test = testdir.makepyfile('def test_pass(_sensitive_skipping): pass')
    testdir.quick_qa('--destructive', file_test, skipped=1)


def test_run_destructive_when_forced_and_not_sensitive(testdir):
    file_test = testdir.makepyfile('def test_pass(_sensitive_skipping): pass')
    testdir.quick_qa('--destructive', '--sensitive-url=foo', file_test,
                     passed=1)
