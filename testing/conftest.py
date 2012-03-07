#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from webserver import SimpleWebServer

pytest_plugins = 'pytester'


def pytest_sessionstart(session):
    webserver = SimpleWebServer()
    webserver.start()
    WebServer.webserver = webserver


def pytest_sessionfinish(session, exitstatus):
    WebServer.webserver.stop()


def pytest_internalerror(excrepr):
    WebServer.webserver.stop()


def pytest_keyboard_interrupt(excinfo):
    WebServer.webserver.stop()


class WebServer:

    pass
