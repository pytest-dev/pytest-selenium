# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


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
                   '--driver', 'SauceLabs')


def test_missing_username(failure):
    out = failure()
    assert 'UsageError: Sauce Labs username must be set' in out


def test_missing_api_key(failure, monkeypatch):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    out = failure()
    assert 'UsageError: Sauce Labs API key must be set' in out


def test_invalid_credentials(failure, monkeypatch):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')
    failure('--capability', 'browserName', 'Firefox')
