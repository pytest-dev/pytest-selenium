# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from _pytest.mark import MarkInfo
from py.xml import html
import pytest
import requests
from selenium import webdriver

from .base import CloudProvider


class Provider(CloudProvider):

    @property
    def name(self):
        return 'Sauce Labs'

    def _username(self, config):
        username = config.getini('sauce_labs_username')
        if not username:
            raise pytest.UsageError('Sauce Labs username must be set')
        return username

    def _api_key(self, config):
        api_key = config.getini('sauce_labs_api_key')
        if not api_key:
            raise pytest.UsageError('Sauce Labs API key must be set')
        return api_key

    def start_driver(self, item, capabilities):
        keywords = item.keywords
        marks = [m for m in keywords.keys() if isinstance(
            keywords[m], MarkInfo)]
        test_id = '.'.join(self.split_class_and_test_names(item.nodeid))
        capabilities['name'] = test_id
        tags = capabilities.get('tags', []) + marks
        if tags:
            capabilities['tags'] = tags
        executor = 'http://{0}:{1}@ondemand.saucelabs.com:80/wd/hub'.format(
            self._username(item.config), self._api_key(item.config))
        return webdriver.Remote(command_executor=executor,
                                desired_capabilities=capabilities)

    def url(self, config, session):
        return 'http://saucelabs.com/jobs/{0}'.format(session)

    def additional_html(self, session):
        return self._video_html(session)

    def update_status(self, config, session, passed):
        username = self._username(config)
        api_key = self._api_key(config)
        status = {'passed': passed}
        requests.put('http://saucelabs.com/rest/v1/{0}/jobs/{1}'.format(
            username, session),
            data=json.dumps(status), auth=(username, api_key))

    def _video_html(self, session):
        flash_vars = 'config={{\
            "clip":{{\
                "url":"https://assets.saucelabs.com/jobs/{0}/video.flv",\
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
            "playerId":"player{0}",\
            "playlist":[{{\
                "url":"https://assets.saucelabs.com/jobs/{0}/video.flv",\
                "provider":"streamer",\
                "autoPlay":false,\
                "autoBuffering":true}}]}}'.format(session)

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
            id='player{0}'.format(session),
            style='border:1px solid #e6e6e6; float:right; height:240px;'
                  'margin-left:5px; overflow:hidden; width:320px'))
