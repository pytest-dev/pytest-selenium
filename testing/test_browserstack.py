# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.fixture
def testfile(testdir):
    return testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """)


def failure_with_output(testdir, *args, **kwargs):
    reprec = testdir.inline_run(*args, **kwargs)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    return out


@pytest.fixture
def failure(testdir, testfile, httpserver_base_url):
    return partial(failure_with_output, testdir, testfile, httpserver_base_url,
                   '--driver', 'BrowserStack')


def test_missing_username(failure):
    out = failure()
    assert 'UsageError: BrowserStack username must be set' in out


def test_missing_access_key(failure, monkeypatch):
    monkeypatch.setenv('BROWSERSTACK_USERNAME', 'foo')
    out = failure()
    assert 'UsageError: BrowserStack access key must be set' in out


@pytest.mark.skipif(reason='Frequent timeouts occurring with BrowserStack')
def test_invalid_credentials(failure, monkeypatch):
    monkeypatch.setenv('BROWSERSTACK_USERNAME', 'foo')
    monkeypatch.setenv('BROWSERSTACK_ACCESS_KEY', 'bar')
    out = failure()
    assert 'Invalid username or password' in out
