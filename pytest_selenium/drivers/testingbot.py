# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests

from hashlib import md5
from py.xml import html
from pytest_selenium.drivers.cloud import Provider

HOST = "hub.testingbot.com"
PORT = 443


class TestingBot(Provider):

    API = "https://api.testingbot.com/v1/tests/{session}"
    JOB = "http://testingbot.com/members/tests/{session}"

    def __init__(self, host=None, port=None):
        super(TestingBot, self).__init__()
        self.host = host
        self.port = port

    @property
    def auth(self):
        return self.key, self.secret

    @property
    def executor(self):
        return "{1}://{0.host}:{0.port}/wd/hub".format(
            self, "http" if self.host == "localhost" else "https"
        )

    @property
    def key(self):
        return self.get_credential("key", ["TESTINGBOT_KEY", "TESTINGBOT_USR"])

    @property
    def secret(self):
        return self.get_credential("secret", ["TESTINGBOT_SECRET", "TESTINGBOT_PSW"])


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    provider = TestingBot()
    if not provider.uses_driver(item.config.getoption("driver")):
        return

    session_id = item._driver.session_id
    auth_url = get_auth_url(
        "https://testingbot.com/tests/{}.mp4".format(session_id), provider, session_id
    )
    pytest_html = item.config.pluginmanager.getplugin("html")
    extra.append(pytest_html.extras.html(_video_html(auth_url, session_id)))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    provider = TestingBot()
    if not provider.uses_driver(item.config.getoption("driver")):
        return

    passed = report.passed or (report.failed and hasattr(report, "wasxfail"))
    session_id = item._driver.session_id

    # Add the job URL to the summary
    job_url = provider.JOB.format(session=session_id)
    summary.append("{0} Job: {1}".format(provider.name, job_url))
    pytest_html = item.config.pluginmanager.getplugin("html")
    # Add the job URL to the HTML report
    extra.append(pytest_html.extras.url(job_url, "{0} Job".format(provider.name)))

    try:
        # Update the job result
        api_url = provider.API.format(session=session_id)
        job_info = requests.get(api_url, auth=provider.auth, timeout=10).json()
        if report.when == "setup" or job_info.get("success") is not False:
            # Only update the result if it's not already marked as failed
            data = {"test[success]": "1" if passed else "0"}
            requests.put(api_url, data=data, auth=provider.auth, timeout=10)
    except Exception as e:
        summary.append(
            "WARNING: Failed to update {0} job status: {1}".format(provider.name, e)
        )


def driver_kwargs(request, test, capabilities, host, port, **kwargs):
    provider = TestingBot(host, port)

    capabilities.setdefault("name", test)
    capabilities.setdefault("client_key", provider.key)
    capabilities.setdefault("client_secret", provider.secret)
    markers = [x.name for x in request.node.iter_markers()]
    groups = capabilities.get("groups", []) + markers
    if groups:
        capabilities["groups"] = groups
    kwargs = {
        "command_executor": provider.executor,
        "desired_capabilities": capabilities,
    }
    return kwargs


def _video_html(video_url, session):
    return str(
        html.div(
            html.video(
                html.source(src=video_url, type="video/mp4"),
                width="100%",
                height="100%",
                controls="controls",
            ),
            id="mediaplayer{session}".format(session=session),
            style="border:1px solid #e6e6e6; float:right; height:240px;"
            "margin-left:5px; overflow:hidden; width:320px",
        )
    )


def get_auth_url(url, provider, session_id):
    key = "{0.key}:{0.secret}:{1}".format(provider, session_id)
    token = md5(key.encode("utf-8")).hexdigest()
    return "{}?auth={}".format(url, token)
