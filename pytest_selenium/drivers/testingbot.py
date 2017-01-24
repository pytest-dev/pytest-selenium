# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from _pytest.mark import MarkInfo
from py.xml import html
import requests

from pytest_selenium.drivers.cloud import Provider


class TestingBot(Provider):

    API = 'https://api.testingbot.com/v1/tests/{session}'
    JOB = 'http://testingbot.com/members/tests/{session}'

    @property
    def auth(self):
        return (self.key, self.secret)

    @property
    def executor(self):
        return 'http://{0}:{1}@hub.testingbot.com/wd/hub'.format(
            self.key, self.secret)

    @property
    def key(self):
        return self.get_credential('key', 'TESTINGBOT_KEY')

    @property
    def secret(self):
        return self.get_credential('secret', 'TESTINGBOT_SECRET')


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    provider = TestingBot()
    if item.config.getoption('driver') != provider.driver:
        return

    pytest_html = item.config.pluginmanager.getplugin('html')
    extra.append(pytest_html.extras.html(_video_html(item._driver.session_id)))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    provider = TestingBot()
    if item.config.getoption('driver') != provider.driver:
        return

    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))
    session_id = item._driver.session_id

    # Add the job URL to the summary
    job_url = provider.JOB.format(session=session_id)
    summary.append('{0} Job: {1}'.format(provider.name, job_url))
    pytest_html = item.config.pluginmanager.getplugin('html')
    # Add the job URL to the HTML report
    extra.append(pytest_html.extras.url(job_url, '{0} Job'.format(
        provider.name)))

    try:
        # Update the job result
        api_url = provider.API.format(session=session_id)
        job_info = requests.get(api_url, auth=provider.auth, timeout=10).json()
        if report.when == 'setup' or job_info.get('success') is not False:
            # Only update the result if it's not already marked as failed
            data = {'test[success]': '1' if passed else '0'}
            requests.put(api_url, data=data, auth=provider.auth, timeout=10)
    except Exception as e:
        summary.append('WARNING: Failed to update {0} job status: {1}'.format(
            provider.name, e))


def driver_kwargs(request, test, capabilities, **kwargs):
    provider = TestingBot()
    keywords = request.node.keywords
    capabilities.setdefault('name', test)
    markers = [m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)]
    groups = capabilities.get('groups', []) + markers
    if groups:
        capabilities['groups'] = groups
    kwargs = {
        'command_executor': provider.executor,
        'desired_capabilities': capabilities}
    return kwargs


def _video_html(session):
    flash_vars = 'config={{\
        "clip":{{\
            "url":"{session}",\
            "provider":"rtmp"}},\
        "plugins":{{\
            "controls":{{\
                "url":"http://testingbot.com/assets/\
                    flowplayer.controls-3.2.14.swf",\
                "mute":null,\
                "volume":null}},\
            "rtmp":{{\
                "url":"http://testingbot.com/assets/\
                    flowplayer.rtmp-3.2.11.swf",\
                "netConnectionUrl":"rtmp://s2tuay45tyrz3f.cloudfront.net/\
                    cfx/st"}}}},\
        "playerId":"mediaplayer{session}",\
        "playlist":[{{\
            "url":"{session}",\
            "provider":"rtmp"}}]}}'.format(session=session)

    return str(html.div(html.object(
        html.param(value='true', name='allowfullscreen'),
        html.param(value='always', name='allowscriptaccess'),
        html.param(value='high', name='quality'),
        html.param(value='#000000', name='bgcolor'),
        html.param(value='opaque', name='wmode'),
        html.param(
            value=flash_vars.replace(' ', ''),
            name='flashvars'),
        width='100%',
        height='100%',
        type='application/x-shockwave-flash',
        data='http://testingbot.com/assets/flowplayer-3.2.14.swf',
        name='mediaplayer_api',
        id='mediaplayer_api'),
        id='mediaplayer{session}'.format(session=session),
        style='border:1px solid #e6e6e6; float:right; height:240px;'
              'margin-left:5px; overflow:hidden; width:320px'))
