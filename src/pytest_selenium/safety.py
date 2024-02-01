# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import os
import re

import pytest


def pytest_addoption(parser):
    parser.addini(
        "sensitive_url", help="regular expression for identifying sensitive urls."
    )

    group = parser.getgroup("safety", "safety")
    group._addoption(
        "--sensitive-url", help="regular expression for identifying sensitive urls."
    )


def pytest_configure(config):
    config.option.sensitive_url = (
        config.getoption("sensitive_url")
        or config.getini("sensitive_url")
        or os.getenv("SENSITIVE_URL")
        or ".*"
    )
    config.addinivalue_line(
        "markers",
        "nondestructive: mark the test as nondestructive. "
        "Tests are assumed to be destructive unless this marker is "
        "present. This reduces the risk of running destructive tests "
        "accidentally.",
    )


def pytest_report_header(config, start_path):
    base_url = config.getoption("base_url")
    sensitive_url = config.getoption("sensitive_url")
    msg = "sensitiveurl: {0}".format(sensitive_url)
    if base_url and sensitive_url and re.search(sensitive_url, base_url):
        msg += " *** WARNING: sensitive url matches {} ***".format(base_url)
    return msg


@pytest.fixture(scope="session")
def sensitive_url(request, base_url):
    """Return the first sensitive URL from response history of the base URL"""
    if not base_url:
        return False
    # consider this environment sensitive if the base url or any redirection
    # history matches the regular expression
    urls = [base_url]

    # lazy import requests for projects that don't need requests
    import requests

    try:
        response = requests.get(base_url, timeout=10)
        urls.append(response.url)
        urls.extend([history.url for history in response.history])
    except requests.exceptions.RequestException:
        pass  # ignore exceptions if this URL is unreachable
    search = partial(re.search, request.config.getoption("sensitive_url"))
    matches = list(map(search, urls))
    if any(matches):
        # return the first match
        first_match = next(x for x in matches if x)
        return first_match.string


@pytest.fixture(scope="function", autouse=True)
def _skip_sensitive(request, sensitive_url):
    """Skip destructive tests if the environment is considered sensitive"""
    destructive = "nondestructive" not in request.node.keywords
    if sensitive_url and destructive:
        pytest.skip(
            "This test is destructive and the target URL is "
            "considered a sensitive environment. If this test is "
            "not destructive, add the 'nondestructive' marker to "
            "it. Sensitive URL: {0}".format(sensitive_url)
        )
