# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import ExitStack as does_not_raise
from functools import partial

import pytest_selenium
import pytest

from pytest_selenium.utils import CaseInsensitiveDict

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
    return partial(failure_with_output, testdir, testfile, httpserver_base_url)


def test_driver_case_insensitive(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(request):
            assert request.config.getoption('driver') == 'SaUcELaBs'
    """
    )
    testdir.quick_qa("--driver", "SaUcELaBs", file_test, passed=1)


def test_missing_driver(failure):
    out = failure()
    assert "UsageError: --driver must be specified" in out


def test_invalid_driver(testdir):
    testdir.makepyfile(
        """
            import pytest
            @pytest.mark.nondestructive
            def test_pass(): pass
        """
    )
    invalid_driver = "noop"
    result = testdir.runpytest("--driver", invalid_driver)
    message = "--driver: invalid choice: '{}'".format(invalid_driver)
    assert message in result.errlines[1]


def test_driver_quit(testdir):
    testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_driver_quit(selenium):
            selenium.quit()
            selenium.title
    """
    )
    result = testdir.runpytestqa()
    result.stdout.fnmatch_lines_random(
        [
            "WARNING: Failed to gather URL: *",
            "WARNING: Failed to gather screenshot: *",
            "WARNING: Failed to gather HTML: *",
            "WARNING: Failed to gather log types: *",
        ]
    )
    outcomes = result.parseoutcomes()
    assert outcomes.get("failed") == 1


def test_default_host_port(testdir):
    host = "localhost"
    port = "4444"
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert driver_kwargs['command_executor'] == 'http://{}:{}/wd/hub'
    """.format(
            host, port
        )
    )
    testdir.quick_qa("--driver", "Remote", file_test, passed=1)


@pytest.mark.parametrize(
    ("host_arg_name", "port_arg_name", "context"),
    [
        ("--selenium-host", "--selenium-port", does_not_raise()),
        ("--host", "--port", pytest.warns(DeprecationWarning)),
    ],
)
def test_arguments_order(testdir, host_arg_name, port_arg_name, context):
    host = "notlocalhost"
    port = "4441"
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert driver_kwargs['command_executor'] == 'http://{}:{}/wd/hub'
    """.format(
            host, port
        )
    )
    with context:
        testdir.quick_qa(
            "--driver",
            "Remote",
            host_arg_name,
            host,
            port_arg_name,
            port,
            file_test,
            passed=1,
        )


def test_arguments_order_random(testdir):
    host = "notlocalhost"
    port = "4441"
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert driver_kwargs['command_executor'] == 'http://{}:{}/wd/hub'
    """.format(
            host, port
        )
    )
    testdir.quick_qa(
        "--selenium-host",
        host,
        "--driver",
        "Remote",
        "--selenium-port",
        port,
        file_test,
        passed=1,
    )


@pytest.mark.parametrize(
    "name", ["SauceLabs", "TestingBot", "CrossBrowserTesting", "BrowserStack"]
)
def test_provider_naming(name):
    import importlib

    driver = name
    module = importlib.import_module(
        "pytest_selenium.drivers.{}".format(driver.lower())
    )
    provider = getattr(module, driver)()
    assert provider.uses_driver(driver)
    assert provider.name == name


def test_service_log_path(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert driver_kwargs['service_log_path'] is not None
    """
    )
    testdir.quick_qa("--driver", "Firefox", file_test, passed=1)


def test_no_service_log_path(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.fixture
        def driver_log():
            return None

        @pytest.mark.nondestructive
        def test_pass(driver_kwargs):
            assert driver_kwargs['service_log_path'] is None
    """
    )
    testdir.quick_qa("--driver", "Firefox", file_test, passed=1)


def test_driver_retry_pass(testdir, mocker):
    mocker.patch.dict(
        pytest_selenium.SUPPORTED_DRIVERS,
        CaseInsensitiveDict({"Firefox": mocker.MagicMock()}),
    )
    mock_retrying = mocker.spy(pytest_selenium.pytest_selenium, "Retrying")

    file_test = testdir.makepyfile(
        """
        import pytest

        @pytest.mark.nondestructive
        def test_pass(driver):
            assert driver
    """
    )

    testdir.quick_qa("--driver", "Firefox", file_test, passed=1)
    assert mock_retrying.spy_return.statistics["attempt_number"] == 1


@pytest.mark.parametrize("max_num_attempts", [None, 2])
def test_driver_retry_fail(testdir, mocker, max_num_attempts):
    mocker.patch(
        "pytest_selenium.webdriver.firefox.webdriver.FirefoxRemoteConnection",
        side_effect=Exception("Connection Error"),
    )
    mocker.patch("pytest_selenium.webdriver.firefox.webdriver.Service")
    mocker.patch("pytest_selenium.pytest_selenium.wait_exponential", return_value=0)
    mock_retrying = mocker.spy(pytest_selenium.pytest_selenium, "Retrying")

    default_attempts = 3
    if max_num_attempts is not None:
        testdir.makeini(
            f"""
            [pytest]
            max_driver_init_attempts = {max_num_attempts}
            """
        )

    file_test = testdir.makepyfile(
        """
        import pytest

        @pytest.mark.nondestructive
        def test_pass(driver):
            assert True  # catch if this starts to pass
        """
    )

    testdir.quick_qa("--driver", "Firefox", file_test, failed=1)
    expected_attempts = max_num_attempts or default_attempts
    assert mock_retrying.spy_return.statistics["attempt_number"] == expected_attempts


def test_xdist(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest

        @pytest.mark.nondestructive
        def test_xdist(driver):
            pass
    """
    )
    testdir.quick_qa("--driver", "firefox", "-n", "2", file_test, passed=1)
