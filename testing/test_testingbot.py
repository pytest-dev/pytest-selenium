# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest
import sys

from functools import partial

from pytest_selenium.drivers.cloud import Provider

"'as TB' to avoid pytest trying to collect the class"
from pytest_selenium.drivers.testingbot import HOST, PORT, TestingBot as TB

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
        "TestingBot",
    )


def test_missing_key(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    assert "TestingBot key must be set" in failure()


def test_missing_secret_env(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    monkeypatch.setenv("TESTINGBOT_KEY", "foo")
    assert "TestingBot secret must be set" in failure()


def test_missing_secret_file(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    tmpdir.join(".testingbot").write("[credentials]\nkey=foo")
    assert "TestingBot secret must be set" in failure()


@pytest.mark.parametrize(
    ("key", "secret"),
    [("TESTINGBOT_KEY", "TESTINGBOT_SECRET"), ("TESTINGBOT_PSW", "TESTINGBOT_USR")],
)
def test_invalid_credentials_env(failure, monkeypatch, tmpdir, key, secret):
    monkeypatch.setenv(key, "foo")
    monkeypatch.setenv(secret, "bar")
    out = failure()
    messages = ["incorrect TestingBot credentials", "basic auth failed"]
    assert any(message in out for message in messages)


def test_invalid_credentials_file(failure, monkeypatch, tmpdir):
    cfg_file = tmpdir.join(".testingbot")
    cfg_file.write("[credentials]\nkey=foo\nsecret=bar")
    monkeypatch.setattr(Provider, "config_file_path", str(cfg_file))
    out = failure()
    messages = ["incorrect TestingBot credentials", "basic auth failed"]
    assert any(message in out for message in messages)


@pytest.mark.skipif(sys.platform == "win32", reason="Fails on Windows for some reason")
def test_invalid_host(failure, monkeypatch, tmpdir):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmpdir))
    tmpdir.join(".testingbot").write("[credentials]\nkey=foo\nsecret=bar")
    out = failure("--selenium-host", "foo.bar.com")
    messages = [
        "nodename nor servname provided, or not known",
        "Name or service not known",
        "No address associated with hostname",
        "No such host is known",
    ]
    assert any(message in out for message in messages)


@pytest.mark.parametrize(
    ("protocol", "host", "port"), [("http", "localhost", "4445"), ("https", HOST, PORT)]
)
def test_executor_url(protocol, host, port):
    assert TB(host, port).executor == "{}://{}:{}/wd/hub".format(protocol, host, port)
