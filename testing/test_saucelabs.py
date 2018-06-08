# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os

import pytest

pytestmark = [pytest.mark.skip_selenium, pytest.mark.nondestructive]


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


def test_missing_username(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    assert 'SauceLabs username must be set' in failure()


def test_missing_api_key_env(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    assert 'SauceLabs key must be set' in failure()


def test_missing_api_key_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    tmpdir.join('.saucelabs').write('[credentials]\nusername=foo')
    assert 'SauceLabs key must be set' in failure()


@pytest.mark.parametrize(('username', 'key'), [('SAUCELABS_USERNAME',
                                                'SAUCELABS_API_KEY'),
                                               ('SAUCELABS_USR',
                                                'SAUCELABS_PSW'),
                                               ('SAUCE_USERNAME',
                                                'SAUCE_ACCESS_KEY')])
def test_invalid_credentials_env(failure, monkeypatch, tmpdir, username, key):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    monkeypatch.setenv(username, 'foo')
    monkeypatch.setenv(key, 'bar')
    out = failure()
    messages = ['Sauce Labs Authentication Error', 'basic auth failed']
    assert any(message in out for message in messages)


def test_invalid_credentials_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    tmpdir.join('.saucelabs').write('[credentials]\nusername=foo\nkey=bar')
    out = failure()
    messages = ['Sauce Labs Authentication Error', 'basic auth failed']
    assert any(message in out for message in messages)


def test_auth_type_none(monkeypatch):
    from pytest_selenium.drivers.saucelabs import SauceLabs, get_job_url

    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')

    session_id = '123456'
    expected = 'https://saucelabs.com/jobs/{}'.format(session_id)
    actual = get_job_url(Config('none'), SauceLabs(), session_id)
    assert actual == expected


@pytest.mark.parametrize('auth_type', ['token', 'day', 'hour'])
def test_auth_type_expiration(monkeypatch, auth_type):
    import re
    from pytest_selenium.drivers.saucelabs import SauceLabs, get_job_url

    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')

    session_id = '123456'
    expected_pattern = r'https://saucelabs\.com/jobs/' \
                       r'{}\?auth=[a-f0-9]{{32}}$'.format(session_id)
    actual = get_job_url(Config(auth_type), SauceLabs(), session_id)
    assert re.match(expected_pattern, actual)


class Config(object):

    def __init__(self, value):
        self._value = value

    def getini(self, key):
        if key == 'saucelabs_job_auth':
            return self._value
        else:
            raise KeyError
