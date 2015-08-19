# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os
import re

import pytest
import requests


def pytest_addoption(parser):
    group = parser.getgroup('safety', 'safety')
    group._addoption('--sensitive-url',
                     default=os.environ.get('SELENIUM_SENSITIVE_URL', '.*'),
                     help='regular expression for identifying sensitive urls.'
                          ' (default: %default)')
    group._addoption('--destructive',
                     action='store_true',
                     dest='run_destructive',
                     help='include destructive tests (tests '
                          'not explicitly marked as \'nondestructive\').'
                          ' (default: %default)')


def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave
    config.addinivalue_line(
        'markers', 'nondestructive: mark the test as nondestructive. '
        'Tests are assumed to be destructive unless this marker is '
        'present. This reduces the risk of running destructive tests '
        'accidentally.')
    if not config.option.run_destructive:
        if config.option.markexpr:
            # preserve a user configured mark expression
            config.option.markexpr = 'nondestructive and (%s)' % \
                config.option.markexpr
        else:
            config.option.markexpr = 'nondestructive'


@pytest.fixture(scope='session')
def sensitive_url(request, base_url):
    """Return the first sensitive URL from response history of the base URL"""
    # consider this environment sensitive if the base url or any redirection
    # history matches the regular expression
    response = requests.get(base_url)
    urls = [history.url for history in response.history] + [response.url]
    search = partial(re.search, request.config.option.sensitive_url)
    matches = map(search, urls)
    if any(matches):
        # return the first match
        first_match = next(x for x in matches if x)
        return first_match.string


@pytest.fixture(scope='function')
def skip_sensitive(request, sensitive_url):
    """Skip destructive tests if the environment is considered sensitive"""
    destructive = 'nondestructive' not in request.node.keywords
    if sensitive_url and destructive:
        pytest.skip(
            'This test is destructive and the target URL is '
            'considered a sensitive environment. If this test is '
            'not destructive, add the \'nondestructive\' marker to '
            'it. Sensitive URL: {0}'.format(sensitive_url))
