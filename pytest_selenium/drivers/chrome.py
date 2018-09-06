# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from distutils.version import LooseVersion

import pytest
from selenium import __version__ as SELENIUM_VERSION
from selenium.webdriver.chrome.options import Options


def driver_kwargs(
    capabilities, driver_args, driver_log, driver_path, chrome_options, **kwargs
):
    kwargs = {"desired_capabilities": capabilities, "service_log_path": driver_log}

    # Selenium 3.8.0 deprecated chrome_options in favour of options
    if LooseVersion(SELENIUM_VERSION) < LooseVersion("3.8.0"):
        kwargs["chrome_options"] = chrome_options
    else:
        kwargs["options"] = chrome_options

    if driver_args is not None:
        kwargs["service_args"] = driver_args
    if driver_path is not None:
        kwargs["executable_path"] = driver_path
    return kwargs


@pytest.fixture
def chrome_options():
    return Options()
