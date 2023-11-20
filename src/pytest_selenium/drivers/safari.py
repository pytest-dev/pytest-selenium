# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from selenium.webdriver.safari.options import Options
from selenium.webdriver.safari.service import Service


def driver_kwargs(safari_options, safari_service, **kwargs):
    return {
        "options": safari_options,
        "service": safari_service,
    }


@pytest.fixture
def safari_options():
    return Options()


@pytest.fixture
def safari_service(driver_path, driver_args, driver_log):
    return Service(
        executable_path=driver_path, service_args=driver_args, log_output=driver_log
    )
