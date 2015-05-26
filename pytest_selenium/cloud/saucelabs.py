# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from _pytest.mark import MarkInfo
from py.xml import html
import pytest
import requests
from selenium import webdriver


name = 'Sauce Labs'


def _credentials(config):
    username = config.getini('sauce_labs_username')
    api_key = config.getini('sauce_labs_api_key')
    if not username:
        raise pytest.UsageError('Sauce Labs username must be set')
    if not api_key:
        raise pytest.UsageError('Sauce Labs API key must be set')
    return username, api_key


def _split_class_and_test_names(nodeid):
    # TODO remove duplication of shared code
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def start_driver(item, capabilities):
    options = item.config.option
    keywords = item.keywords
    marks = [m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)]
    tags = item.config.getini('sauce_labs_tags') + marks
    try:
        job_visibility = item.keywords['sauce_labs_job_visibility'].args[0]
    except (IndexError, KeyError):
        # mark is not present or has no value
        job_visibility = item.config.getini('sauce_labs_job_visibility')

    if options.browser_name is None:
        raise pytest.UsageError('Sauce Labs requires a browser name')

    test_id = '.'.join(_split_class_and_test_names(item.nodeid))
    capabilities.update({
        'name': test_id,
        'public': job_visibility,
        'browserName': options.browser_name})
    if options.build is not None:
        capabilities['build'] = options.build
    if tags is not None and len(tags) > 0:
        capabilities['tags'] = tags
    if options.platform is not None:
        capabilities['platform'] = options.platform
    if options.browser_version is not None:
        capabilities['version'] = options.browser_version
    executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % \
        _credentials(item.config)
    return webdriver.Remote(command_executor=executor,
                            desired_capabilities=capabilities)


def url(config, session):
    return 'http://saucelabs.com/jobs/%s' % session


def additional_html(session):
    return [_video_html(session)]


def update_status(config, session, passed):
    username, api_key = _credentials(config)
    status = {'passed': passed}
    requests.put(
        'http://saucelabs.com//rest/v1/%s/jobs/%s' % (username, session),
        data=json.dumps(status), auth=(username, api_key))


def _video_html(session):
    flash_vars = 'config={\
        "clip":{\
            "url":"https://assets.saucelabs.com/jobs/%(session)s/video.flv",\
            "provider":"streamer",\
            "autoPlay":false,\
            "autoBuffering":true},\
        "play": {\
            "opacity":1,\
            "label":null,\
            "replayLabel":null},\
        "plugins":{\
            "streamer":{\
                "url":"https://cdn1.saucelabs.com/sauce_skin_deprecated/lib/flowplayer/flowplayer.pseudostreaming-3.2.13.swf",\
                "queryString":"%%3Fstart%%3D%%24%%7Bstart%%7D"},\
            "controls":{\
                "mute":false,\
                "volume":false,\
                "backgroundColor":"rgba(0,0,0,0.7)"}},\
        "playerId":"player%(session)s",\
        "playlist":[{\
            "url":"https://assets.saucelabs.com/jobs/%(session)s/video.flv",\
            "provider":"streamer",\
            "autoPlay":false,\
            "autoBuffering":true}]}' % {'session': session}

    return html.div(html.object(
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
        data='https://cdn1.saucelabs.com/sauce_skin_deprecated/lib/flowplayer/'
             'flowplayer-3.2.17.swf',
        name='player_api',
        id='player_api'),
        id='player%s' % session,
        style='border:1px solid #e6e6e6; float:right; height:240px;'
              'margin-left:5px; overflow:hidden; width:320px')
