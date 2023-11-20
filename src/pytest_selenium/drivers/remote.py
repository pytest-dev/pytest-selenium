# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

HOST = os.environ.get("SELENIUM_HOST", "localhost")
PORT = os.environ.get("SELENIUM_PORT", 4444)


def driver_kwargs(remote_options, host, port, **kwargs):
    host = host if host.startswith("http") else f"http://{host}"
    executor = f"{host}:{port}/wd/hub"

    return {
        "command_executor": executor,
        "options": remote_options,
    }


@pytest.fixture
def remote_options(chrome_options, firefox_options, edge_options, capabilities):
    browser = capabilities.get("browserName", "").upper()
    if browser == "CHROME":
        return chrome_options
    elif browser == "FIREFOX":
        return firefox_options
    elif browser == "EDGE":
        return edge_options
