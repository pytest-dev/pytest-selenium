# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def driver_kwargs(chrome_options, chrome_service, **kwargs):
    return {"options": chrome_options, "service": chrome_service}


@pytest.fixture
def chrome_options():
    return Options()


@pytest.fixture
def chrome_service(driver_path, driver_args, driver_log):
    return Service(
        executable_path=driver_path, service_args=driver_args, log_output=driver_log
    )
