# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os
import datetime

import pytest

monkeytime = datetime.datetime(2020, 12, 25, 17)

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


def test_missing_username(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    assert 'Sauce Labs username must be set' in failure()


def test_missing_api_key_env(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    assert 'Sauce Labs key must be set' in failure()


def test_missing_api_key_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmpdir))
    tmpdir.join('.saucelabs').write('[credentials]\nusername=foo')
    assert 'Sauce Labs key must be set' in failure()


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


USERNAME = 'foo'
API_KEY = 'bar'
SESSION_ID = '12345678'
TOKEN = '{}:{}{}+{}'.format(USERNAME, API_KEY, '{}', SESSION_ID)


@pytest.mark.parametrize(('auth_type', 'auth_token'),
                         [('none', ''),
                          ('token', TOKEN),
                          ('day', TOKEN),
                          ('hour', TOKEN)])
def test_auth_token(monkeypatch, auth_type, auth_token):
    import datetime
    import hmac
    from pytest_selenium.drivers.saucelabs import SauceLabs, get_job_url

    monkeypatch.setattr(datetime, 'datetime', MonkeyDatetime)
    monkeypatch.setattr(hmac, 'new', hmac_new)
    monkeypatch.setenv('SAUCELABS_USERNAME', USERNAME)
    monkeypatch.setenv('SAUCELABS_API_KEY', API_KEY)

    url = 'https://saucelabs.com/jobs/{}'.format(SESSION_ID)

    time_format = None
    if auth_type == 'token':
        auth_token = auth_token.format('')
    elif auth_type == 'hour':
        time_format = '%Y-%m-%d-%H'
    elif auth_type == 'day':
        time_format = '%Y-%m-%d'

    if time_format:
        monkey = MonkeyDatetime().utcnow().strftime(time_format)
        auth_token = auth_token.format(':' + monkey)

    if auth_type != 'none':
        url += '?auth={}'.format(auth_token)

    result = get_job_url(Config(auth_type), SauceLabs(), SESSION_ID)
    assert result == url


def hmac_new(key, msg, _):
    return HMAC(key, msg)


class HMAC:

    def __init__(self, key, msg):
        self._digest = key.decode('utf-8') + '+' + msg.decode('utf-8')

    def hexdigest(self):
        return self._digest


class MonkeyDatetime:

    @classmethod
    def utcnow(cls):
        return monkeytime


class Config(object):

    def __init__(self, value):
        self._value = value

    def getini(self, key):
        if key == 'saucelabs_job_auth':
            return self._value
        else:
            raise KeyError
