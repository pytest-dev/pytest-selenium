# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from py.xml import html
import pytest
import requests

from pytest_selenium.drivers.cloud import Provider


class CrossBrowserTesting(Provider):

    API = "https://crossbrowsertesting.com/api/v3/selenium/{session}"

    @property
    def auth(self):
        return self.username, self.key

    @property
    def executor(self):
        return "https://hub.crossbrowsertesting.com/wd/hub"

    @property
    def username(self):
        return self.get_credential(
            "username", ["CROSSBROWSERTESTING_USERNAME", "CROSSBROWSERTESTING_USR"]
        )

    @property
    def key(self):
        return self.get_credential(
            "key", ["CROSSBROWSERTESTING_AUTH_KEY", "CROSSBROWSERTESTING_PSW"]
        )


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    provider = CrossBrowserTesting()
    if not provider.uses_driver(item.config.getoption("driver")):
        return

    videos = (
        requests.get(
            provider.API.format(session=item._driver.session_id),
            auth=provider.auth,
            timeout=10,
        )
        .json()
        .get("videos")
    )

    if videos and len(videos) > 0:
        pytest_html = item.config.pluginmanager.getplugin("html")
        extra.append(pytest_html.extras.html(_video_html(videos[0])))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    provider = CrossBrowserTesting()
    if not provider.uses_driver(item.config.getoption("driver")):
        return

    passed = report.passed or (report.failed and hasattr(report, "wasxfail"))

    # Add the test URL to the summary
    info = requests.get(
        provider.API.format(session=item._driver.session_id),
        auth=provider.auth,
        timeout=10,
    ).json()

    url = info.get("show_result_public_url")
    summary.append("{0}: {1}".format(provider.name, url))
    pytest_html = item.config.pluginmanager.getplugin("html")
    # Add the job URL to the HTML report
    extra.append(pytest_html.extras.url(url, provider.name))

    try:
        # Update the test result
        if report.when == "setup" or info.get("test_score") != "fail":
            # Only update the result if it's not already marked as failed
            score = "pass" if passed else "fail"
            data = {"action": "set_score", "score": score}
            r = requests.put(
                provider.API.format(session=info.get("selenium_test_id")),
                data=data,
                auth=provider.auth,
                timeout=10,
            )
            r.raise_for_status()
    except Exception as e:
        summary.append(
            "WARNING: Failed to update {0} job status: {1}".format(provider.name, e)
        )


def driver_kwargs(request, test, capabilities, **kwargs):
    provider = CrossBrowserTesting()
    capabilities.setdefault("name", test)
    capabilities.setdefault("username", provider.username)
    capabilities.setdefault("password", provider.key)
    kwargs = {
        "command_executor": provider.executor,
        "desired_capabilities": capabilities,
    }
    return kwargs


def _video_html(video):
    html.__tagspec__.update(dict([(x, 1) for x in ("video", "source")]))
    video_attrs = {
        "controls": "",
        "poster": video.get("image"),
        "play-pause-on-click": "",
        "style": "border:1px solid #e6e6e6; float:right; height:240px; "
        "margin-left:5px; overflow:hidden; width:320px",
    }
    source_attrs = {"src": video.get("video"), "type": "video/mp4"}
    return str(html.video(html.source(**source_attrs), **video_attrs))
