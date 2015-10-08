# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.fixture
def testfile(testdir):
    return testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(): pass
    """)


def failure_with_output(testdir, *args, **kwargs):
    reprec = testdir.inline_run(*args, **kwargs)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    return out


def test_ignore_bad_url(testdir, testfile, webserver):
    base_url = 'http://localhost:{0}/500'.format(webserver.port)
    testdir.quick_qa('--base-url', base_url, testfile, passed=1)


def test_enable_verify_via_cli(testdir, testfile, webserver, monkeypatch):
    monkeypatch.setenv('VERIFY_BASE_URL', False)
    status_code = 500
    base_url = 'http://localhost:{0}/{1}'.format(webserver.port, status_code)
    out = failure_with_output(testdir, testfile, '--base-url', base_url,
                              '--verify-base-url')
    assert 'UsageError: Base URL failed verification!' in out
    assert 'URL: {0}'.format(base_url) in out
    assert 'Response status code: {0}'.format(status_code) in out
    assert 'Response headers: ' in out


def test_enable_verify_via_env(testdir, testfile, webserver, monkeypatch):
    monkeypatch.setenv('VERIFY_BASE_URL', True)
    status_code = 500
    base_url = 'http://localhost:{0}/{1}'.format(webserver.port, status_code)
    out = failure_with_output(testdir, testfile, '--base-url', base_url)
    assert 'UsageError: Base URL failed verification!' in out
    assert 'URL: {0}'.format(base_url) in out
    assert 'Response status code: {0}'.format(status_code) in out
    assert 'Response headers: ' in out


def test_disable_verify_via_env(testdir, testfile, webserver, monkeypatch):
    monkeypatch.setenv('VERIFY_BASE_URL', False)
    base_url = 'http://localhost:{0}/500'.format(webserver.port)
    testdir.quick_qa('--base-url', base_url, testfile, passed=1)
