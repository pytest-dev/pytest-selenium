# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ConfigParser import ConfigParser
import os
import json

from py.xml import html
import pytest
import requests
from selenium import webdriver


name = 'Sauce Labs'


def _get_config(option):
    config = ConfigParser()
    config.read('setup.cfg')
    section = 'saucelabs'
    if config.has_section(section) and config.has_option(section, option):
        return config.get(section, option)


def _credentials():
    username = os.getenv('SAUCELABS_USERNAME', _get_config('username'))
    api_key = os.getenv('SAUCELABS_API_KEY', _get_config('api-key'))
    if not username:
        raise pytest.UsageError('Sauce Labs username must be set')
    if not api_key:
        raise pytest.UsageError('Sauce Labs API key must be set')
    return username, api_key


def _tags():
    tags = _get_config('tags')
    if tags:
        return tags.split(',')
    return []


def _split_class_and_test_names(nodeid):
    # TODO remove duplication of shared code
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def start_driver(item, options, capabilities):
    from _pytest.mark import MarkInfo
    tags = _tags() + [m for m in item.keywords.keys() if isinstance(
        item.keywords[m], MarkInfo)]
    try:
        privacy = item.keywords['privacy'].args[0]
    except (IndexError, KeyError):
        # privacy mark is not present or has no value
        privacy = _get_config('privacy')

    if options.browser_name is None:
        raise pytest.UsageError('Sauce Labs requires a browser name')

    test_id = '.'.join(_split_class_and_test_names(item.nodeid))
    capabilities.update({
        'name': test_id,
        'public': privacy,
        'browserName': options.browser_name})
    if options.build is not None:
        capabilities['build'] = options.build
    if tags is not None and len(tags) > 0:
        capabilities['tags'] = tags
    if options.platform is not None:
        capabilities['platform'] = options.platform
    if options.browser_version is not None:
        capabilities['version'] = options.browser_version
    executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % _credentials()
    return webdriver.Remote(command_executor=executor,
                            desired_capabilities=capabilities)


def url(session):
    return 'http://saucelabs.com/jobs/%s' % session


def additional_html(session):
    return [_video_html(session)]


def update_status(session, passed):
    username, api_key = _credentials()
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
