# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


def test_skip_destructive_by_default(testdir):
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa(file_test, passed=0, failed=0, skipped=1)


def test_warn_when_url_is_sensitive(testdir, monkeypatch, capsys):
    monkeypatch.setenv("SENSITIVE_URL", r"webserver")
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa(file_test, "--verbose", passed=0, failed=0, skipped=1)
    out, err = capsys.readouterr()
    msg = "*** WARNING: sensitive url matches http://webserver ***"
    assert msg in out


def test_skip_destructive_when_sensitive_command_line(testdir):
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa(
        "--sensitive-url", "webserver", file_test, passed=0, failed=0, skipped=1
    )


def test_skip_destructive_when_sensitive_config_file(testdir):
    testdir.makefile(".ini", pytest="[pytest]\nsensitive_url=webserver")
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa(file_test, passed=0, failed=0, skipped=1)


def test_skip_destructive_when_sensitive_env(testdir, monkeypatch):
    monkeypatch.setenv("SENSITIVE_URL", "webserver")
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa(file_test, passed=0, failed=0, skipped=1)


def test_run_non_destructive_by_default(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(): pass
    """
    )
    testdir.quick_qa(file_test, passed=1)


def test_run_destructive_when_not_sensitive_command_line(testdir):
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa("--sensitive-url", "foo", file_test, passed=1)


def test_run_destructive_when_not_sensitive_config_file(testdir):
    testdir.makefile(".ini", pytest="[pytest]\nsensitive_url=foo")
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa(file_test, passed=1, failed=0, skipped=0)


def test_run_destructive_when_not_sensitive_env(testdir, monkeypatch):
    monkeypatch.setenv("SENSITIVE_URL", "foo")
    file_test = testdir.makepyfile("def test_pass(): pass")
    testdir.quick_qa(file_test, passed=1, failed=0, skipped=0)


def test_run_destructive_and_non_destructive_when_not_sensitive(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass1(): pass
        def test_pass2(): pass
    """
    )
    testdir.quick_qa("--sensitive-url", "foo", file_test, passed=2)
