# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os
import json

import pytest

from pytest_selenium.drivers.cloud import Provider

pytestmark = pytest.mark.nondestructive


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
        "BrowserStack",
    )


def test_missing_username(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    assert "BrowserStack username must be set" in failure()


def test_missing_access_key_env(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    monkeypatch.setenv("BROWSERSTACK_USERNAME", "foo")
    assert "BrowserStack key must be set" in failure()


def test_missing_access_key_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    tmpdir.join(".browserstack").write("[credentials]\nusername=foo")
    assert "BrowserStack key must be set" in failure()


@pytest.mark.parametrize(
    ("username", "key"),
    [
        ("BROWSERSTACK_USERNAME", "BROWSERSTACK_ACCESS_KEY"),
        ("BROWSERSTACK_USR", "BROWSERSTACK_PSW"),
    ],
)
def test_invalid_credentials_env(failure, monkeypatch, tmpdir, username, key):
    monkeypatch.setenv(username, "foo")
    monkeypatch.setenv(key, "bar")
    out = failure()
    messages = [
        "Invalid username or password",
        "basic auth failed",
        "Authorization required",
    ]
    assert any(message in out for message in messages)


def test_invalid_credentials_file(failure, monkeypatch, tmpdir):
    cfg_file = tmpdir.join(".browserstack")
    cfg_file.write("[credentials]\nusername=foo\nkey=bar")
    monkeypatch.setattr(Provider, "config_file_path", str(cfg_file))
    out = failure()
    messages = [
        "Invalid username or password",
        "basic auth failed",
        "Authorization required",
    ]
    assert any(message in out for message in messages)


def test_invalid_job_access_value(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    tmpdir.join(".browserstack").write("[report]\njob_access=foo")
    assert "BrowserStack job_access invalid value `foo`" in failure()


def test_default_caps_in_jsonwp(monkeypatch, testdir):
    capabilities = {"browserName": "chrome"}
    test_name = "test_default_caps_in_jsonwp.test_bstack_capabilities"
    monkeypatch.setenv("BROWSERSTACK_USERNAME", "foo")
    monkeypatch.setenv("BROWSERSTACK_ACCESS_KEY", "bar")
    variables = testdir.makefile(
        ".json", '{{"capabilities": {}}}'.format(json.dumps(capabilities))
    )
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_bstack_capabilities(driver_kwargs):
            assert driver_kwargs['options'].capabilities['browserstack.user'] == 'foo'
            assert driver_kwargs['options'].capabilities['browserstack.key'] == 'bar'
            assert driver_kwargs['options'].capabilities['name'] == '{0}'
    """.format(
            test_name
        )
    )
    testdir.quick_qa(
        "--driver", "BrowserStack", "--variables", variables, file_test, passed=1
    )


def test_default_caps_in_jsonwp_with_conflict(monkeypatch, testdir):
    capabilities = {"browserName": "chrome", "name": "conflicting_name"}
    monkeypatch.setenv("BROWSERSTACK_USERNAME", "foo")
    monkeypatch.setenv("BROWSERSTACK_ACCESS_KEY", "bar")
    variables = testdir.makefile(
        ".json", '{{"capabilities": {}}}'.format(json.dumps(capabilities))
    )
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_bstack_capabilities(driver_kwargs):
            assert driver_kwargs['options'].capabilities['browserstack.user'] == 'foo'
            assert driver_kwargs['options'].capabilities['browserstack.key'] == 'bar'
            assert driver_kwargs['options'].capabilities['name'] == 'conflicting_name'
    """
    )
    testdir.quick_qa(
        "--driver", "BrowserStack", "--variables", variables, file_test, passed=1
    )


def test_default_caps_in_W3C(monkeypatch, testdir):
    capabilities = {"browserName": "chrome", "bstack:options": {}}
    monkeypatch.setenv("BROWSERSTACK_USERNAME", "foo")
    monkeypatch.setenv("BROWSERSTACK_ACCESS_KEY", "bar")
    variables = testdir.makefile(
        ".json", '{{"capabilities": {}}}'.format(json.dumps(capabilities))
    )
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_bstack_capabilities(driver_kwargs):
            assert driver_kwargs['options'].capabilities['bstack:options'] == {
                'userName': 'foo',
                'accessKey': 'bar',
                'sessionName': 'test_default_caps_in_W3C.test_bstack_capabilities'
            }
    """
    )
    testdir.quick_qa(
        "--driver", "BrowserStack", "--variables", variables, file_test, passed=1
    )


def test_default_caps_in_W3C_with_conflict(monkeypatch, testdir):
    capabilities = {
        "browserName": "chrome",
        "bstack:options": {"sessionName": "conflicting_name"},
    }
    monkeypatch.setenv("BROWSERSTACK_USERNAME", "foo")
    monkeypatch.setenv("BROWSERSTACK_ACCESS_KEY", "bar")
    variables = testdir.makefile(
        ".json", '{{"capabilities": {}}}'.format(json.dumps(capabilities))
    )
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_bstack_capabilities(driver_kwargs):
            assert driver_kwargs['options'].capabilities['bstack:options'] == {
                'userName': 'foo',
                'accessKey': 'bar',
                'sessionName': 'conflicting_name'
            }
    """
    )
    testdir.quick_qa(
        "--driver", "BrowserStack", "--variables", variables, file_test, passed=1
    )
