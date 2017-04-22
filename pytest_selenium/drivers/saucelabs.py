# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from _pytest.mark import MarkInfo
from py.xml import html
import pytest
import requests

from pytest_selenium.drivers.cloud import Provider


class SauceLabs(Provider):

    API = 'http://saucelabs.com/rest/v1/{username}/jobs/{session}'
    JOB = 'http://saucelabs.com/jobs/{session}'

    @property
    def auth(self):
        return (self.username, self.key)

    @property
    def executor(self):
        return 'http://{0}:{1}@ondemand.saucelabs.com:80/wd/hub'.format(
            self.username, self.key)

    @property
    def name(self):
        return 'Sauce Labs'

    @property
    def username(self):
        return self.get_credential('username', ['SAUCELABS_USERNAME',
                                                'SAUCELABS_USR'])

    @property
    def key(self):
        return self.get_credential('key', ['SAUCELABS_API_KEY',
                                           'SAUCELABS_PSW'])


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    provider = SauceLabs()
    if item.config.getoption('driver') != provider.driver:
        return

    pytest_html = item.config.pluginmanager.getplugin('html')
    extra.append(pytest_html.extras.html(_video_html(item._driver.session_id)))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    provider = SauceLabs()
    if item.config.getoption('driver') != provider.driver:
        return

    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))
    session_id = item._driver.session_id

    # Add the job URL to the summary
    provider = SauceLabs()
    job_url = provider.JOB.format(session=session_id)
    summary.append('{0} Job: {1}'.format(provider.name, job_url))
    pytest_html = item.config.pluginmanager.getplugin('html')
    # Add the job URL to the HTML report
    extra.append(pytest_html.extras.url(job_url, '{0} Job'.format(
        provider.name)))

    try:
        # Update the job result
        api_url = provider.API.format(
            session=session_id,
            username=provider.username)
        job_info = requests.get(api_url, auth=provider.auth, timeout=10).json()
        if report.when == 'setup' or job_info.get('passed') is not False:
            # Only update the result if it's not already marked as failed
            data = json.dumps({'passed': passed})
            requests.put(api_url, data=data, auth=provider.auth, timeout=10)
    except Exception as e:
        summary.append('WARNING: Failed to update {0} job status: {1}'.format(
            provider.name, e))


def driver_kwargs(request, test, capabilities, **kwargs):
    provider = SauceLabs()
    keywords = request.node.keywords
    capabilities.setdefault('name', test)
    markers = [m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)]
    tags = capabilities.get('tags', []) + markers
    if tags:
        capabilities['tags'] = tags
    kwargs = {
        'command_executor': provider.executor,
        'desired_capabilities': capabilities}
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
            "autoBuffering":true}}]}}'.format(session=session)

    return str(html.div(html.object(
        html.param(value='true', name='allowfullscreen'),
        html.param(value='always', name='allowscriptaccess'),
        html.param(value='high', name='quality'),
        html.param(value='#000000', name='bgcolor'),
        html.param(
            value=flash_vars.replace(' ', ''),
            name='flashvars'),
        width='100%',
        height='100%',
        type='application/x-shockwave-flash',
        data='https://cdn1.saucelabs.com/sauce_skin_deprecated/lib/'
             'flowplayer/flowplayer-3.2.17.swf',
        name='player_api',
        id='player_api'),
        id='player{session}'.format(session=session),
        style='border:1px solid #e6e6e6; float:right; height:240px;'
              'margin-left:5px; overflow:hidden; width:320px'))
