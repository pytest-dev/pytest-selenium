# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from selenium.webdriver.chrome.options import Options


def driver_kwargs(
    capabilities, driver_args, driver_log, driver_path, chrome_options, **kwargs
):
    kwargs = {
        "desired_capabilities": capabilities,
        "service_log_path": driver_log,
        "options": chrome_options,
    }

    if driver_args is not None:
        kwargs["service_args"] = driver_args
    if driver_path is not None:
        kwargs["executable_path"] = driver_path
    return kwargs


@pytest.fixture
def chrome_options():
    return Options()
