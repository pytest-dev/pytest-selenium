# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import ConfigParser
from py.xml import html
import requests
from selenium import webdriver


class SauceLabs(object):

    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key

    def driver(self, test_id, capabilities, options, keywords):
        config = ConfigParser.ConfigParser(defaults={
            'tags': '',
            'privacy': 'public restricted'})
        config.read('mozwebqa.cfg')
        tags = config.get('DEFAULT', 'tags').split(',')
        from _pytest.mark import MarkInfo
        tags.extend([m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)])
        try:
            privacy = keywords['privacy'].args[0]
        except (IndexError, KeyError):
            # privacy mark is not present or has no value
            privacy = config.get('DEFAULT', 'privacy')

        capabilities.update({
            'build': options.build,
            'name': test_id,
            'tags': tags,
            'public': privacy,
            'browserName': options.browser_name})

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
