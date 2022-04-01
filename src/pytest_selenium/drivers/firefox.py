# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

import pytest

from selenium.webdriver.firefox.options import Options

LOGGER = logging.getLogger(__name__)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "firefox_arguments(args): arguments to be passed to "
        "Firefox. This marker will be ignored for other browsers. For "
        "example: firefox_arguments('-foreground')",
    )
    config.addinivalue_line(
        "markers",
        "firefox_preferences(dict): preferences to be passed to "
        "Firefox. This marker will be ignored for other browsers. For "
        "example: firefox_preferences({'browser.startup.homepage': "
        "'https://pytest.org/'})",
    )


def driver_kwargs(capabilities, driver_log, driver_path, firefox_options, **kwargs):
    kwargs = {"service_log_path": driver_log}

    if capabilities:
        kwargs["capabilities"] = capabilities
    if driver_path is not None:
        kwargs["executable_path"] = driver_path

    kwargs["options"] = firefox_options

    return kwargs


@pytest.fixture
def firefox_options(request):
    options = Options()

    for arg in get_arguments_from_markers(request.node):
        options.add_argument(arg)

    for name, value in get_preferences_from_markers(request.node).items():
        options.set_preference(name, value)

    return options


def get_arguments_from_markers(node):
    arguments = []
    for m in node.iter_markers("firefox_arguments"):
        arguments.extend(m.args)
    return arguments


def get_preferences_from_markers(node):
    preferences = dict()
    for mark in node.iter_markers("firefox_preferences"):
        preferences.update(mark.args[0])
    return preferences
