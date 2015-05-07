# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ConfigParser import ConfigParser
import os
import json

from py.xml import html
import requests
from selenium import webdriver


class SauceLabs(object):

    def __init__(self):
        username = None
        api_key = None

        self.tags = []
        self.privacy = 'public restricted'

        config = ConfigParser()
        # TODO support reading from ~/.saucelabs
        config.read('setup.cfg')

        section = 'saucelabs'
        if config.has_section(section):
            if config.has_option(section, 'username'):
                username = config.get(section, 'username')
            if config.has_option(section, 'api-key'):
                api_key = config.get(section, 'api-key')
            if config.has_option(section, 'tags'):
                self.tags = config.get(section, 'tags').split(',')
            if config.has_option(section, 'privacy'):
                self.privacy = config.get(section, 'privacy')

        self.username = os.getenv('SAUCELABS_USERNAME', username)
        self.api_key = os.getenv('SAUCELABS_API_KEY', api_key)

        if self.username is None:
            raise ValueError('Sauce Labs username must be set!')
        if self.api_key is None:
            raise ValueError('Sauce Labs API key must be set!')

    def driver(self, test_id, capabilities, options, keywords):
        from _pytest.mark import MarkInfo
        tags = self.tags + [m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)]
        try:
            privacy = keywords['privacy'].args[0]
        except (IndexError, KeyError):
            # privacy mark is not present or has no value
            privacy = self.privacy

        capabilities.update({
            'name': test_id,
            'public': privacy,
            'browserName': options.browser_name})

        if options.build is not None:
            capabilities['build'] = options.build

        if tags:
            capabilities['tags'] = tags

        if options.platform is not None:
            capabilities['platform'] = options.platform

        if options.browser_version is not None:
            capabilities['version'] = options.browser_version

        executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (
            self.username, self.api_key)
        return webdriver.Remote(command_executor=executor,
                                desired_capabilities=capabilities)

    @property
    def name(self):
        return 'Sauce Labs'

    def url(self, session):
        return 'http://saucelabs.com/jobs/%s' % session

    def additional_html(self, session):
        return [self._video_html(session)]

    def update_status(self, session, passed):
        status = {'passed': passed}
        requests.put('http://saucelabs.com//rest/v1/%s/jobs/%s' % (self.username, session),
                     data=json.dumps(status), auth=(self.username, self.api_key))

    def _video_html(self, session):
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
            data='https://cdn1.saucelabs.com/sauce_skin_deprecated/lib/flowplayer/flowplayer-3.2.17.swf',
            name='player_api',
            id='player_api'),
            id='player%s' % session,
            style='border:1px solid #e6e6e6; float:right; height:240px;'
                  'margin-left:5px; overflow:hidden; width:320px')
