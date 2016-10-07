# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os

from _pytest.mark import MarkInfo
from py.xml import html
import pytest
import requests

DRIVER = 'SauceLabs'
API_JOB_URL = 'http://saucelabs.com/rest/v1/{username}/jobs/{session}'
EXECUTOR_URL = 'http://{username}:{key}@ondemand.saucelabs.com:80/wd/hub'
JOB_URL = 'http://saucelabs.com/jobs/{session}'


def pytest_addoption(parser):
    parser.addini('sauce_labs_username',
                  help='sauce labs username',
                  default=os.getenv('SAUCELABS_USERNAME'))
    parser.addini('sauce_labs_api_key',
                  help='sauce labs api key',
                  default=os.getenv('SAUCELABS_API_KEY'))


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    if item.config.getoption('driver') != DRIVER:
        return

    pytest_html = item.config.pluginmanager.getplugin('html')
    extra.append(pytest_html.extras.html(_video_html(item._driver.session_id)))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    if item.config.getoption('driver') != DRIVER:
        return

    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))
    session_id = item._driver.session_id

    # Add the job URL to the summary
    job_url = JOB_URL.format(session=session_id)
    summary.append('{0} Job: {1}'.format(DRIVER, job_url))
    pytest_html = item.config.pluginmanager.getplugin('html')
    # Add the job URL to the HTML report
    extra.append(pytest_html.extras.url(job_url, '{0} Job'.format(DRIVER)))

    try:
        # Update the job result
        username = _username(item.config)
        auth = (username, _api_key(item.config))
        api_url = API_JOB_URL.format(username=username, session=session_id)
        job_info = requests.get(api_url, auth=auth, timeout=10).json()
        if report.when == 'setup' or job_info.get('passed') is not False:
            # Only update the result if it's not already marked as failed
            data = json.dumps({'passed': passed})
            requests.put(api_url, data=data, auth=auth, timeout=10)
    except Exception as e:
        summary.append('WARNING: Failed to update {0} job status: {1}'.format(
            DRIVER, e))


def driver_kwargs(request, test, capabilities, **kwargs):
    keywords = request.node.keywords
    capabilities.setdefault('name', test)
    markers = [m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)]
    tags = capabilities.get('tags', []) + markers
    if tags:
        capabilities['tags'] = tags
    executor = EXECUTOR_URL.format(
        username=_username(request.config),
        key=_api_key(request.config))
    kwargs = {
        'command_executor': executor,
        'desired_capabilities': capabilities}
    return kwargs


def _api_key(config):
    api_key = config.getini('sauce_labs_api_key')
    if not api_key:
        raise pytest.UsageError('Sauce Labs API key must be set')
    return api_key


def _username(config):
    username = config.getini('sauce_labs_username')
    if not username:
        raise pytest.UsageError('Sauce Labs username must be set')
    return username


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
