# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os
import json

import pytest

from pytest_selenium.drivers.cloud import Provider

pytestmark = [pytest.mark.skip_selenium, pytest.mark.nondestructive]


@pytest.fixture
def testfile(testdir):
    return testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """
    )


def failure_with_output(testdir, *args, **kwargs):
    reprec = testdir.inline_run(*args, **kwargs)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    return out


@pytest.fixture
def failure(testdir, testfile, httpserver_base_url):
    return partial(
        failure_with_output,
        testdir,
        testfile,
        httpserver_base_url,
        "--driver",
        "SauceLabs",
    )


def test_missing_username(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    assert "SauceLabs username must be set" in failure()


def test_missing_api_key_env(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    monkeypatch.setenv("SAUCELABS_USERNAME", "foo")
    assert "SauceLabs key must be set" in failure()


def test_missing_api_key_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    tmpdir.join(".saucelabs").write("[credentials]\nusername=foo")
    assert "SauceLabs key must be set" in failure()


@pytest.mark.parametrize(
    ("username", "key"),
    [
        ("SAUCELABS_USERNAME", "SAUCELABS_API_KEY"),
        ("SAUCELABS_USR", "SAUCELABS_PSW"),
        ("SAUCE_USERNAME", "SAUCE_ACCESS_KEY"),
    ],
)
def test_invalid_credentials_env(failure, monkeypatch, tmpdir, username, key):
    monkeypatch.setenv(username, "foo")
    monkeypatch.setenv(key, "bar")
    out = failure()
    messages = ["Sauce Labs Authentication Error", "basic auth failed", "Unauthorized"]
    assert any(message in out for message in messages)


def test_invalid_credentials_file(failure, monkeypatch, tmpdir):
    cfg_file = tmpdir.join(".saucelabs")
    cfg_file.write("[credentials]\nusername=foo\nkey=bar")
    monkeypatch.setattr(Provider, "config_file_path", str(cfg_file))
    out = failure()
    messages = ["Sauce Labs Authentication Error", "basic auth failed", "Unauthorized"]
    assert any(message in out for message in messages)


def test_credentials_in_capabilities(monkeypatch, testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_sauce_capabilities(driver_kwargs):
            assert driver_kwargs['desired_capabilities']['username'] == 'foo'
            assert driver_kwargs['desired_capabilities']['accessKey'] == 'bar'
    """
    )

    run_sauce_test(monkeypatch, testdir, file_test)


def test_no_sauce_options(monkeypatch, testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_sauce_capabilities(driver_kwargs):
            try:
                driver_kwargs['desired_capabilities']['sauce:options']
                raise AssertionError('<sauce:options> should not be present!')
            except KeyError:
                pass
    """
    )

    run_sauce_test(monkeypatch, testdir, file_test)


def run_sauce_test(monkeypatch, testdir, file_test):
    monkeypatch.setenv("SAUCELABS_USERNAME", "foo")
    monkeypatch.setenv("SAUCELABS_API_KEY", "bar")

    capabilities = {"browserName": "chrome"}
    variables = testdir.makefile(
        ".json", '{{"capabilities": {}}}'.format(json.dumps(capabilities))
    )

    testdir.quick_qa(
        "--driver", "saucelabs", "--variables", variables, file_test, passed=1
    )


def test_empty_sauce_options(monkeypatch, testdir):
    capabilities = {"browserName": "chrome"}
    expected = {"name": "test_empty_sauce_options.test_sauce_capabilities"}
    run_w3c_sauce_test(capabilities, expected, monkeypatch, testdir)


def test_merge_sauce_options(monkeypatch, testdir):
    version = {"seleniumVersion": "3.8.1"}
    capabilities = {"browserName": "chrome", "sauce:options": version}
    expected = {"name": "test_merge_sauce_options.test_sauce_capabilities"}
    expected.update(version)
    run_w3c_sauce_test(capabilities, expected, monkeypatch, testdir)


def test_merge_sauce_options_with_conflict(monkeypatch, testdir):
    name = "conflict"
    capabilities = {"browserName": "chrome", "sauce:options": {"name": name}}
    expected = {"name": name}
    run_w3c_sauce_test(capabilities, expected, monkeypatch, testdir)


def run_w3c_sauce_test(capabilities, expected_result, monkeypatch, testdir):
    username = "foo"
    access_key = "bar"

    monkeypatch.setenv("SAUCELABS_USERNAME", username)
    monkeypatch.setenv("SAUCELABS_API_KEY", access_key)
    monkeypatch.setenv("SAUCELABS_W3C", "true")

    expected_result.update(
        {"username": username, "accessKey": access_key, "tags": ["nondestructive"]}
    )

    variables = testdir.makefile(
        ".json", '{{"capabilities": {}}}'.format(json.dumps(capabilities))
    )

    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_sauce_capabilities(driver_kwargs):
            actual = driver_kwargs['desired_capabilities']['sauce:options']
            assert actual == {}
    """.format(
            expected_result
        )
    )

    testdir.quick_qa(
        "--driver", "saucelabs", "--variables", variables, file_test, passed=1
    )


def test_auth_type_none(monkeypatch):
    from pytest_selenium.drivers.saucelabs import SauceLabs, get_job_url

    monkeypatch.setenv("SAUCELABS_USERNAME", "foo")
    monkeypatch.setenv("SAUCELABS_API_KEY", "bar")

    session_id = "123456"
    expected = "https://api.us-west-1.saucelabs.com/v1/jobs/{}".format(session_id)
    actual = get_job_url(Config("none"), SauceLabs(), session_id)
    assert actual == expected


@pytest.mark.parametrize("auth_type", ["token", "day", "hour"])
def test_auth_type_expiration(monkeypatch, auth_type):
    import re
    from pytest_selenium.drivers.saucelabs import SauceLabs, get_job_url

    monkeypatch.setenv("SAUCELABS_USERNAME", "foo")
    monkeypatch.setenv("SAUCELABS_API_KEY", "bar")

    session_id = "123456"
    expected_pattern = (
        r"https://api.us-west-1.saucelabs\.com/v1/jobs/"
        r"{}\?auth=[a-f0-9]{{32}}$".format(session_id)
    )
    actual = get_job_url(Config(auth_type), SauceLabs(), session_id)
    assert re.match(expected_pattern, actual)


def test_data_center_option(testdir, monkeypatch):
    monkeypatch.setenv("SAUCELABS_USERNAME", "foo")
    monkeypatch.setenv("SAUCELABS_API_KEY", "bar")

    expected_data_center = "us-east-1"
    testdir.makeini(
        f"""
        [pytest]
        saucelabs_data_center = {expected_data_center}
    """
    )

    file_test = testdir.makepyfile(
        f"""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert "{expected_data_center}" in driver_kwargs['command_executor']
    """
    )
    testdir.quick_qa("--driver", "SauceLabs", file_test, passed=1)


def test_data_center_option_file(testdir, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    monkeypatch.setenv("SAUCELABS_USERNAME", "foo")
    monkeypatch.setenv("SAUCELABS_API_KEY", "bar")

    expected_data_center = "us-east-1"
    tmpdir.join(".saucelabs").write(f"[options]\ndata_center={expected_data_center}")

    file_test = testdir.makepyfile(
        f"""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert "{expected_data_center}" in driver_kwargs['command_executor']
    """
    )
    testdir.quick_qa("--driver", "SauceLabs", file_test, passed=1)


def test_data_center_option_precedence(testdir, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    monkeypatch.setenv("SAUCELABS_USERNAME", "foo")
    monkeypatch.setenv("SAUCELABS_API_KEY", "bar")

    expected_data_center = "us-east-1"
    tmpdir.join(".saucelabs").write(f"[options]\ndata_center={expected_data_center}")

    testdir.makeini(
        """
        [pytest]
        saucelabs_data_center = "ap-east-1"
    """
    )

    file_test = testdir.makepyfile(
        f"""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert "{expected_data_center}" in driver_kwargs['command_executor']
    """
    )
    testdir.quick_qa("--driver", "SauceLabs", file_test, passed=1)


class Config(object):
    def __init__(self, value):
        self._value = value

    def getini(self, key):
        if key == "saucelabs_job_auth":
            return self._value
        else:
            raise KeyError
