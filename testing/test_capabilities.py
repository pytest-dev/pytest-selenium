# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.fixture
def testfile(testdir):
    return testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_capabilities(capabilities):
            assert capabilities['foo'] == 'bar'
    """)


def test_command_line(testfile, testdir):
    testdir.quick_qa('--capability', 'foo', 'bar', testfile, passed=1)


def test_file(testfile, testdir):
    variables = testdir.makefile('.json', '{"capabilities": {"foo": "bar"}}')
    testdir.quick_qa('--variables', variables, testfile, passed=1)


def test_file_remote(testdir):
    key = 'goog:chromeOptions'
    capabilities = {'browserName': 'chrome', key: {'args': ['foo']}}
    variables = testdir.makefile('.json', '{{"capabilities": {}}}'.format(
        json.dumps(capabilities)))
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_capabilities(session_capabilities, capabilities):
            assert session_capabilities['{0}']['args'] == ['foo']
            assert capabilities['{0}']['args'] == ['foo']
    """.format(key))
    testdir.quick_qa(
        '--driver', 'Remote', '--variables', variables, file_test, passed=1)


def test_fixture(testfile, testdir):
    testdir.makeconftest("""
        import pytest
        @pytest.fixture(scope='session')
        def capabilities():
            return {'foo': 'bar'}
    """)
    testdir.quick_qa(testfile, passed=1)


def test_mark(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        @pytest.mark.capabilities(foo='bar')
        def test_capabilities(session_capabilities, capabilities):
            assert 'foo' not in session_capabilities
            assert capabilities['foo'] == 'bar'
    """)
    testdir.quick_qa(file_test, passed=1)


def test_no_sauce_options(monkeypatch, testdir):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')

    capabilities = {'browserName': 'chrome'}
    variables = testdir.makefile('.json', '{{"capabilities": {}}}'.format(
        json.dumps(capabilities)))

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

    testdir.quick_qa(
        '--driver', 'saucelabs', '--variables',
        variables, file_test, passed=1)


def test_empty_sauce_options(monkeypatch, testdir):
    capabilities = {'browserName': 'chrome'}
    expected = {'name': 'test_empty_sauce_options.test_sauce_capabilities',
                'tags': ['nondestructive']}
    run_sauce_test(capabilities, expected, monkeypatch, testdir)


def test_merge_sauce_options(monkeypatch, testdir):
    version = {'seleniumVersion': '3.8.1'}
    capabilities = {'browserName': 'chrome', 'sauce:options': version}
    expected = {'name': 'test_merge_sauce_options.test_sauce_capabilities',
                'tags': ['nondestructive']}
    expected.update(version)
    run_sauce_test(capabilities, expected, monkeypatch, testdir)


def test_merge_sauce_options_with_conflict(monkeypatch, testdir):
    name = 'conflict'
    capabilities = {'browserName': 'chrome', 'sauce:options': {'name': name}}
    expected = {'name': name, 'tags': ['nondestructive']}
    run_sauce_test(capabilities, expected, monkeypatch, testdir)


def run_sauce_test(capabilities, expected_result, monkeypatch, testdir):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')
    monkeypatch.setenv('SAUCELABS_W3C', 'true')

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
