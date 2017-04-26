# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os

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


def test_missing_username(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    assert 'BrowserStack username must be set' in failure()


def test_missing_access_key_env(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    monkeypatch.setenv('BROWSERSTACK_USERNAME', 'foo')
    assert 'BrowserStack key must be set' in failure()


def test_missing_access_key_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    tmpdir.join('.browserstack').write('[credentials]\nusername=foo')
    assert 'BrowserStack key must be set' in failure()


@pytest.mark.parametrize(('username', 'key'), [('BROWSERSTACK_USERNAME',
                                                'BROWSERSTACK_ACCESS_KEY'),
                                               ('BROWSERSTACK_USR',
                                                'BROWSERSTACK_PSW')])
def test_invalid_credentials_env(failure, monkeypatch, tmpdir, username, key):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    monkeypatch.setenv(username, 'foo')
    monkeypatch.setenv(key, 'bar')
    out = failure()
    messages = ['Invalid username or password', 'basic auth failed']
    assert any(message in out for message in messages)


def test_invalid_credentials_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    tmpdir.join('.browserstack').write('[credentials]\nusername=foo\nkey=bar')
    out = failure()
    messages = ['Invalid username or password', 'basic auth failed']
    assert any(message in out for message in messages)
