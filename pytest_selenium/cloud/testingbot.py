# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from _pytest.mark import MarkInfo
from py.xml import html
import requests
from selenium import webdriver

from .base import CloudProvider


class Provider(CloudProvider):

    @property
    def name(self):
        return 'TestingBot'

    def _key(self, config):
        key = config.getini('testingbot_key')
        if not key:
            raise pytest.UsageError('TestingBot key must be set')
        return key

    def _secret(self, config):
        secret = config.getini('testingbot_secret')
        if not secret:
            raise pytest.UsageError('TestingBot secret must be set')
        return secret

    def start_driver(self, item, capabilities):
        keywords = item.keywords
        marks = [m for m in keywords.keys() if isinstance(
            keywords[m], MarkInfo)]
        groups = capabilities.get('groups', []) + marks
        test_id = '.'.join(self.split_class_and_test_names(item.nodeid))
        capabilities['name'] = test_id
        if groups:
            capabilities['groups'] = groups

        executor = 'http://{0}:{1}@hub.testingbot.com/wd/hub'.format(
            self._key(item.config), self._secret(item.config))
        return webdriver.Remote(command_executor=executor,
                                desired_capabilities=capabilities)

    def url(self, config, session):
        return 'http://testingbot.com/members/tests/{0}'.format(session)

    def additional_html(self, session):
        return self._video_html(session)

    def update_status(self, config, session, passed):
        requests.put('https://api.testingbot.com/v1/tests/{0}'.format(session),
                     data={'test[success]': '1' if passed else '0'},
                     auth=(self._key(config), self._secret(config)))

    def _video_html(self, session):
        flash_vars = 'config={{\
            "clip":{{\
                "url":"{0}",\
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
            "playerId":"mediaplayer{0}",\
            "playlist":[{{\
                "url":"{0}",\
                "provider":"rtmp"}}]}}'.format(session)

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
            id='mediaplayer{0}'.format(session),
            style='border:1px solid #e6e6e6; float:right; height:240px;'
                  'margin-left:5px; overflow:hidden; width:320px'))
