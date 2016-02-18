# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


def test_skip_destructive_by_default(testdir):
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa(file_test, passed=0, failed=0, skipped=1)


def test_skip_destructive_when_sensitive_command_line(testdir, httpserver):
    file_test = testdir.makepyfile('def test_pass(): pass')
    print(httpserver.url)
    testdir.quick_qa('--sensitive-url', '127\.0\.0\.1', file_test, passed=0,
                     failed=0, skipped=1)


def test_skip_destructive_when_sensitive_config_file(testdir, httpserver):
    testdir.makefile('.ini', pytest='[pytest]\nsensitive_url=127\.0\.0\.1')
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa(file_test, passed=0, failed=0, skipped=1)


def test_skip_destructive_when_sensitive_env(testdir, httpserver, monkeypatch):
    monkeypatch.setenv('SENSITIVE_URL', '127\.0\.0\.1')
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa(file_test, passed=0, failed=0, skipped=1)


def test_run_non_destructive_by_default(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(): pass
    """)
    testdir.quick_qa(file_test, passed=1)


def test_run_destructive_when_not_sensitive_command_line(testdir, httpserver):
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa('--sensitive-url', 'foo', file_test, passed=1)


def test_run_destructive_when_not_sensitive_config_file(testdir, httpserver):
    testdir.makefile('.ini', pytest='[pytest]\nsensitive_url=foo')
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa(file_test, passed=1, failed=0, skipped=0)


def test_run_destructive_when_not_sensitive_env(testdir, httpserver,
                                                monkeypatch):
    monkeypatch.setenv('SENSITIVE_URL', 'foo')
    file_test = testdir.makepyfile('def test_pass(): pass')
    testdir.quick_qa(file_test, passed=1, failed=0, skipped=0)


def test_run_destructive_and_non_destructive_when_not_sensitive(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass1(): pass
        def test_pass2(): pass
    """)
    testdir.quick_qa('--sensitive-url', 'foo', file_test, passed=2)
