# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os
import re

import pytest
import requests


def pytest_addoption(parser):
    parser.addini('sensitive_url',
                  help='regular expression for identifying sensitive urls.')

    group = parser.getgroup('safety', 'safety')
    group._addoption('--sensitive-url',
                     help='regular expression for identifying sensitive urls.')


def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave
    config.addinivalue_line(
        'markers', 'nondestructive: mark the test as nondestructive. '
        'Tests are assumed to be destructive unless this marker is '
        'present. This reduces the risk of running destructive tests '
        'accidentally.')


@pytest.fixture
def sensitive_url(request, base_url):
    """Return the first sensitive URL from response history of the base URL"""
    if not base_url:
        return False
    # consider this environment sensitive if the base url or any redirection
    # history matches the regular expression
    sensitive = '.*'
    config = request.config
    if config.option.sensitive_url:
        sensitive = config.option.sensitive_url
    elif config.getini('sensitive_url'):
        sensitive = config.getini('sensitive_url')
    elif os.getenv('SENSITIVE_URL'):
        sensitive = os.getenv('SENSITIVE_URL')

    urls = [base_url]
    try:
        response = requests.get(base_url, timeout=10)
        urls.append(response.url)
        urls.extend([history.url for history in response.history])
    except requests.exceptions.RequestException:
        pass  # ignore exceptions if this URL is unreachable
    search = partial(re.search, sensitive)
    matches = list(map(search, urls))
    if any(matches):
        # return the first match
        first_match = next(x for x in matches if x)
        return first_match.string


@pytest.fixture
def _skip_sensitive(request, sensitive_url):
    """Skip destructive tests if the environment is considered sensitive"""
    destructive = 'nondestructive' not in request.node.keywords
    if sensitive_url and destructive:
        pytest.skip(
            'This test is destructive and the target URL is '
            'considered a sensitive environment. If this test is '
            'not destructive, add the \'nondestructive\' marker to '
            'it. Sensitive URL: {0}'.format(sensitive_url))
