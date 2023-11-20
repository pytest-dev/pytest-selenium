# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from selenium.webdriver.common.options import ArgOptions

from pytest_selenium.drivers.cloud import Provider
from pytest_selenium.exceptions import MissingCloudSettingError


class BrowserStack(Provider):

    API = "https://api.browserstack.com/automate/sessions/{session}.json"

    @property
    def auth(self):
        return self.username, self.key

    @property
    def executor(self):
        return "https://hub.browserstack.com/wd/hub"

    @property
    def username(self):
        return self.get_credential(
            "username", ["BROWSERSTACK_USERNAME", "BROWSERSTACK_USR"]
        )

    @property
    def key(self):
        return self.get_credential(
            "key", ["BROWSERSTACK_ACCESS_KEY", "BROWSERSTACK_PSW"]
        )

    @property
    def job_access(self):
        """Get job url field, private(required authentication) or public."""
        try:
            field = self.get_setting(
                key="job_access",
                envs=["BROWSERSTACK_JOB_ACCESS"],
                section="report",
                allowed_values=["browser_url", "public_url"],
            )
        except MissingCloudSettingError:
            field = "browser_url"

        return field


@pytest.hookimpl(optionalhook=True)
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    provider = BrowserStack()
    if not provider.uses_driver(item.config.getoption("driver")):
        return

    passed = report.passed or (report.failed and hasattr(report, "wasxfail"))
    session_id = item._driver.session_id
    api_url = provider.API.format(session=session_id)

    # lazy import requests for projects that don't need requests
    import requests

    try:
        job_info = requests.get(api_url, auth=provider.auth, timeout=10).json()
        job_url = job_info["automation_session"][provider.job_access]
        # Add the job URL to the summary
        summary.append("{0} Job: {1}".format(provider.name, job_url))
        pytest_html = item.config.pluginmanager.getplugin("html")
        # Add the job URL to the HTML report
        extra.append(pytest_html.extras.url(job_url, "{0} Job".format(provider.name)))
    except Exception as e:
        summary.append(
            "WARNING: Failed to determine {0} job URL: {1}".format(provider.name, e)
        )

    try:
        # Update the job result
        job_status = job_info["automation_session"]["status"]
        status = "running" if passed else "error"
        if report.when == "teardown" and passed:
            status = "completed"
        if job_status not in ("error", status):
            # Only update the result if it's not already marked as failed
            requests.put(
                api_url,
                headers={"Content-Type": "application/json"},
                params={"status": status},
                auth=provider.auth,
                timeout=10,
            )
    except Exception as e:
        summary.append("WARNING: Failed to update job status: {0}".format(e))


def driver_kwargs(test, capabilities, **kwargs):
    provider = BrowserStack()
    assert provider.job_access
    options = ArgOptions()
    bstack_options = capabilities.pop("bstack:options", None)
    if isinstance(bstack_options, dict):
        bstack_options.setdefault("sessionName", test)
        bstack_options.setdefault("userName", provider.username)
        bstack_options.setdefault("accessKey", provider.key)
        options.set_capability("bstack:options", bstack_options)
    else:
        options.set_capability("name", test)
        options.set_capability("browserstack.user", provider.username)
        options.set_capability("browserstack.key", provider.key)
    return {
        "command_executor": provider.executor,
        "keep_alive": True,
        "options": options,
    }
