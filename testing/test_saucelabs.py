# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os
import datetime
import json

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


def test_credentials_in_capabilities(monkeypatch, testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_sauce_capabilities(driver_kwargs):
            assert driver_kwargs['desired_capabilities']['username'] == 'foo'
            assert driver_kwargs['desired_capabilities']['accessKey'] == 'bar'
    """)

    run_sauce_test(monkeypatch, testdir, file_test)


def test_no_sauce_options(monkeypatch, testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_sauce_capabilities(driver_kwargs):
            try:
                driver_kwargs['desired_capabilities']['sauce:options']
                raise AssertionError('<sauce:options> should not be present!')
            except KeyError:
                pass
    """)

    run_sauce_test(monkeypatch, testdir, file_test)


def run_sauce_test(monkeypatch, testdir, file_test):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')

    capabilities = {'browserName': 'chrome'}
    variables = testdir.makefile('.json', '{{"capabilities": {}}}'.format(
        json.dumps(capabilities)))

    testdir.quick_qa(
        '--driver', 'saucelabs', '--variables',
        variables, file_test, passed=1)


def test_empty_sauce_options(monkeypatch, testdir):
    capabilities = {'browserName': 'chrome'}
    expected = {'name': 'test_empty_sauce_options.test_sauce_capabilities'}
    run_w3c_sauce_test(capabilities, expected, monkeypatch, testdir)


def test_merge_sauce_options(monkeypatch, testdir):
    version = {'seleniumVersion': '3.8.1'}
    capabilities = {'browserName': 'chrome', 'sauce:options': version}
    expected = {'name': 'test_merge_sauce_options.test_sauce_capabilities'}
    expected.update(version)
    run_w3c_sauce_test(capabilities, expected, monkeypatch, testdir)


def test_merge_sauce_options_with_conflict(monkeypatch, testdir):
    name = 'conflict'
    capabilities = {'browserName': 'chrome', 'sauce:options': {'name': name}}
    expected = {'name': name}
    run_w3c_sauce_test(capabilities, expected, monkeypatch, testdir)


def run_w3c_sauce_test(capabilities, expected_result, monkeypatch, testdir):
    username = 'foo'
    access_key = 'bar'

    monkeypatch.setenv('SAUCELABS_USERNAME', username)
    monkeypatch.setenv('SAUCELABS_API_KEY', access_key)
    monkeypatch.setenv('SAUCELABS_W3C', 'true')

    expected_result.update({'username': username,
                            'accessKey': access_key,
                            'tags': ['nondestructive']})

    variables = testdir.makefile('.json', '{{"capabilities": {}}}'.format(
        json.dumps(capabilities)))

    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_sauce_capabilities(driver_kwargs):
            actual = driver_kwargs['desired_capabilities']['sauce:options']
            assert actual == {}
    """.format(expected_result))

    testdir.quick_qa(
        '--driver', 'saucelabs', '--variables',
        variables, file_test, passed=1)


@pytest.mark.parametrize(('auth_type', 'auth_token'),
                         [('none', ''),
                          ('token', '5d5b3d4fe1fcb72edf5f8c431eb10175'),
                          ('day', 'e9480f85e8183e94e39fc69af685831c'),
                          ('hour', '441bac7116b1eeb026fed2a0942aad57')])
def test_auth_token(monkeypatch, auth_type, auth_token):
    import datetime
    from pytest_selenium.drivers.saucelabs import SauceLabs, get_job_url

    monkeypatch.setattr(datetime, 'datetime', MonkeyDatetime)
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')

    session_id = '12345678'
    url = 'https://saucelabs.com/jobs/{}'.format(session_id)

    if auth_type != 'none':
        url += '?auth={}'.format(auth_token)

    result = get_job_url(Config(auth_type), SauceLabs(), session_id)
    assert result == url


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
