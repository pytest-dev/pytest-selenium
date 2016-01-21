# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest
from _pytest.mark import MarkInfo
from py.xml import html
import requests
from selenium.webdriver import Remote

from pytest_selenium import split_class_and_test_names

API_JOB_URL = 'https://api.testingbot.com/v1/tests/{session}'
EXECUTOR_URL = 'http://{key}:{secret}@hub.testingbot.com/wd/hub'
JOB_URL = 'http://testingbot.com/members/tests/{session}'


def pytest_addoption(parser):
    parser.addini('testingbot_key',
                  help='testingbot key',
                  default=os.getenv('TESTINGBOT_KEY'))
    parser.addini('testingbot_secret',
                  help='testingbot secret',
                  default=os.getenv('TESTINGBOT_SECRET'))


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    if item.config.getoption('driver') != 'TestingBot':
        return

    driver = getattr(item, '_driver', None)
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        extra.append(pytest_html.extras.html(_video_html(driver.session_id)))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    if item.config.getoption('driver') != 'TestingBot':
        return

    # Add the job URL to the summary
    driver = getattr(item, '_driver', None)
    job_url = JOB_URL.format(session=driver.session_id)
    summary.append('TestingBot Job: {0}'.format(job_url))
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
        # Add the job URL to the HTML report
        extra.append(pytest_html.extras.url(job_url, 'TestingBot Job'))

    # Update the job result
    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))
    auth = (_key(item.config), _secret(item.config))
    api_url = API_JOB_URL.format(session=driver.session_id)
    job_info = requests.get(api_url, auth=auth, timeout=10).json()
    if report.when == 'setup' or job_info.get('success') is not False:
        # Only update the result if it's not already marked as failed
        data = {'test[success]': '1' if passed else '0'}
        requests.put(api_url, data=data, auth=auth, timeout=10)


@pytest.fixture
def testingbot_driver(request, capabilities):
    """Return a WebDriver using a TestingBot instance"""
    keywords = request.node.keywords
    test_id = '.'.join(split_class_and_test_names(request.node.nodeid))
    capabilities['name'] = test_id
    markers = [m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)]
    groups = capabilities.get('groups', []) + markers
    if groups:
        capabilities['groups'] = groups
    executor = EXECUTOR_URL.format(
        key=_key(request.config),
        secret=_secret(request.config))
    return Remote(command_executor=executor,
                  desired_capabilities=capabilities)


def _key(config):
    key = config.getini('testingbot_key')
    if not key:
        raise pytest.UsageError('TestingBot key must be set')
    return key


def _secret(config):
    secret = config.getini('testingbot_secret')
    if not secret:
        raise pytest.UsageError('TestingBot secret must be set')
    return secret


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
