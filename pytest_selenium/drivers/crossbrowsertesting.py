# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from py.xml import html
import pytest
import requests

DRIVER = 'CrossBrowserTesting'
API_URL = 'https://crossbrowsertesting.com/api/v3/selenium/{session}'
EXECUTOR_URL = 'http://{username}:{key}@hub.crossbrowsertesting.com:80/wd/hub'


def pytest_addoption(parser):
    parser.addini('crossbrowsertesting_username',
                  help='crossbrowsertesting username',
                  default=os.getenv('CROSSBROWSERTESTING_USERNAME'))
    parser.addini('crossbrowsertesting_auth_key',
                  help='crossbrowsertesting auth key',
                  default=os.getenv('CROSSBROWSERTESTING_AUTH_KEY'))


@pytest.mark.optionalhook
def pytest_selenium_capture_debug(item, report, extra):
    if item.config.getoption('driver') != DRIVER:
        return

    videos = requests.get(
        API_URL.format(session=item._driver.session_id),
        auth=_auth(item),
        timeout=10).json().get('videos')

    if videos and len(videos) > 0:
        pytest_html = item.config.pluginmanager.getplugin('html')
        extra.append(pytest_html.extras.html(_video_html(videos[0])))


@pytest.mark.optionalhook
def pytest_selenium_runtest_makereport(item, report, summary, extra):
    if item.config.getoption('driver') != DRIVER:
        return

    passed = report.passed or (report.failed and hasattr(report, 'wasxfail'))

    # Add the test URL to the summary
    info = requests.get(
        API_URL.format(session=item._driver.session_id),
        auth=_auth(item),
        timeout=10).json()

    url = info.get('show_result_public_url')
    summary.append('{0}: {1}'.format(DRIVER, url))
    pytest_html = item.config.pluginmanager.getplugin('html')
    # Add the job URL to the HTML report
    extra.append(pytest_html.extras.url(url, DRIVER))

    try:
        # Update the test result
        if report.when == 'setup' or info.get('test_score') is not 'fail':
            # Only update the result if it's not already marked as failed
            score = 'pass' if passed else 'fail'
            data = {'action': 'set_score', 'score': score}
            r = requests.put(
                API_URL.format(session=info.get('selenium_test_id')),
                data=data,
                auth=_auth(item),
                timeout=10)
            r.raise_for_status()
    except Exception as e:
        summary.append('WARNING: Failed to update {0} job status: {1}'.format(
            DRIVER, e))


def driver_kwargs(request, test, capabilities, **kwargs):
    capabilities.setdefault('name', test)
    executor = EXECUTOR_URL.format(
        username=_username(request.config),
        key=_auth_key(request.config))
    kwargs = {
        'command_executor': executor,
        'desired_capabilities': capabilities}
    return kwargs


def _auth_key(config):
    auth_key = config.getini('crossbrowsertesting_auth_key')
    if not auth_key:
        raise pytest.UsageError('CrossBrowserTesting auth key must be set')
    return auth_key


def _username(config):
    username = config.getini('crossbrowsertesting_username')
    if not username:
        raise pytest.UsageError('CrossBrowserTesting username must be set')
    return username


def _auth(item):
    username = _username(item.config)
    return (username, _auth_key(item.config))


def _video_html(video):
    html.__tagspec__.update(dict([(x, 1) for x in ('video', 'source')]))
    video_attrs = {
        'controls': '',
        'poster': video.get('image'),
        'play-pause-on-click': '',
        'style': 'border:1px solid #e6e6e6; float:right; height:240px; '
                 'margin-left:5px; overflow:hidden; width:320px'}
    source_attrs = {'src': video.get('video'), 'type': 'video/mp4'}
    return str(html.video(
        html.source(**source_attrs),
        **video_attrs))
