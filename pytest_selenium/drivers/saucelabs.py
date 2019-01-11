# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import json

from py.xml import html
import pytest
import requests

from pytest_selenium.drivers.cloud import Provider


class SauceLabs(Provider):

    API = "https://saucelabs.com/rest/v1/{username}/jobs/{session}"
    JOB = "https://saucelabs.com/jobs/{session}"

    @property
    def auth(self):
        return self.username, self.key

    @property
    def executor(self):
        return "https://ondemand.saucelabs.com/wd/hub"

    @property
    def username(self):
        return self.get_credential(
            "username", ["SAUCELABS_USERNAME", "SAUCELABS_USR", "SAUCE_USERNAME"]
        )

    @property
    def key(self):
        return self.get_credential(
            "key", ["SAUCELABS_API_KEY", "SAUCELABS_PSW", "SAUCE_ACCESS_KEY"]
        )

    def uses_driver(self, driver):
        return driver.lower() == self.name.lower()


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    provider = SauceLabs()
    if not provider.uses_driver(item.config.getoption("driver")):
        return

    pytest_html = item.config.pluginmanager.getplugin("html")
    extra.append(pytest_html.extras.html(_video_html(item._driver.session_id)))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    provider = SauceLabs()
    if not provider.uses_driver(item.config.getoption("driver")):
        return

    passed = report.passed or (report.failed and hasattr(report, "wasxfail"))
    session_id = item._driver.session_id

    # Add the job URL to the summary
    provider = SauceLabs()
    job_url = get_job_url(item.config, provider, session_id)
    summary.append("{0} Job: {1}".format(provider.name, job_url))
    pytest_html = item.config.pluginmanager.getplugin("html")
    # Add the job URL to the HTML report
    extra.append(pytest_html.extras.url(job_url, "{0} Job".format(provider.name)))

    try:
        # Update the job result
        api_url = provider.API.format(session=session_id, username=provider.username)
        job_info = requests.get(api_url, auth=provider.auth, timeout=10).json()
        if report.when == "setup" or job_info.get("passed") is not False:
            # Only update the result if it's not already marked as failed
            data = json.dumps({"passed": passed})
            requests.put(api_url, data=data, auth=provider.auth, timeout=10)
    except Exception as e:
        summary.append(
            "WARNING: Failed to update {0} job status: {1}".format(provider.name, e)
        )


def driver_kwargs(request, test, capabilities, **kwargs):
    provider = SauceLabs()

    _capabilities = capabilities
    if os.getenv("SAUCELABS_W3C") == "true":
        _capabilities = capabilities.setdefault("sauce:options", {})

    _capabilities.setdefault("username", provider.username)
    _capabilities.setdefault("accessKey", provider.key)
    _capabilities.setdefault("name", test)
    markers = [x.name for x in request.node.iter_markers()]
    tags = _capabilities.get("tags", []) + markers
    if tags:
        _capabilities["tags"] = tags

    kwargs = {
        "command_executor": provider.executor,
        "desired_capabilities": capabilities,
    }
    return kwargs


def _video_html(session):
    flash_vars = 'config={{\
        "clip":{{\
            "url":"https://assets.saucelabs.com/jobs/{session}/video.flv",\
            "provider":"streamer",\
            "autoPlay":false,\
            "autoBuffering":true}},\
        "play": {{\
            "opacity":1,\
            "label":null,\
            "replayLabel":null}},\
        "plugins":{{\
            "streamer":{{\
                "url":"https://cdn1.saucelabs.com/sauce_skin_deprecated\
                /lib/flowplayer/flowplayer.pseudostreaming-3.2.13.swf",\
                "queryString":"%%3Fstart%%3D%%24%%7Bstart%%7D"}},\
            "controls":{{\
                "mute":false,\
                "volume":false,\
                "backgroundColor":"rgba(0,0,0,0.7)"}}}},\
        "playerId":"player{session}",\
        "playlist":[{{\
            "url":"https://assets.saucelabs.com/jobs/{session}/video.flv",\
            "provider":"streamer",\
            "autoPlay":false,\
            "autoBuffering":true}}]}}'.format(
        session=session
    )

    return str(
        html.div(
            html.object(
                html.param(value="true", name="allowfullscreen"),
                html.param(value="always", name="allowscriptaccess"),
                html.param(value="high", name="quality"),
                html.param(value="#000000", name="bgcolor"),
                html.param(value=flash_vars.replace(" ", ""), name="flashvars"),
                width="100%",
                height="100%",
                type="application/x-shockwave-flash",
                data="https://cdn1.saucelabs.com/sauce_skin_deprecated/lib/"
                "flowplayer/flowplayer-3.2.17.swf",
                name="player_api",
                id="player_api",
            ),
            id="player{session}".format(session=session),
            style="border:1px solid #e6e6e6; float:right; height:240px;"
            "margin-left:5px; overflow:hidden; width:320px",
        )
    )


def get_job_url(config, provider, session_id):
    from datetime import datetime

    job_url = provider.JOB.format(session=session_id)
    job_auth = config.getini("saucelabs_job_auth").lower()

    if job_auth == "none":
        return job_url

    if job_auth == "token":
        return get_auth_url(job_url, provider, session_id)
    elif job_auth == "hour":
        time_format = "%Y-%m-%d-%H"
    elif job_auth == "day":
        time_format = "%Y-%m-%d"
    else:
        raise ValueError("Invalid authorization type: {}".format(job_auth))

    ttl = datetime.utcnow().strftime(time_format)
    return get_auth_url(job_url, provider, session_id, ttl)


def get_auth_url(url, provider, session_id, ttl=None):
    import hmac
    from hashlib import md5

    key = "{0.username}:{0.key}".format(provider)
    if ttl:
        key += ":{}".format(ttl)
    token = hmac.new(key.encode("utf-8"), session_id.encode("utf-8"), md5).hexdigest()
    return "{}?auth={}".format(url, token)
