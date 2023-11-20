# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from selenium.webdriver.ie.options import Options
from selenium.webdriver.ie.service import Service


def driver_kwargs(ie_options, ie_service, **kwargs):
    return {"options": ie_options, "service": ie_service}


@pytest.fixture
def ie_options():
    return Options()


@pytest.fixture
def ie_service(driver_path, driver_args, driver_log):
    return Service(
        executable_path=driver_path, service_args=driver_args, log_output=driver_log
    )
