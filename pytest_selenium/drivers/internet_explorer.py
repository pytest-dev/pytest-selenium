# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from selenium.webdriver import Ie


@pytest.fixture
def ie_driver(request, capabilities, driver_path):
    """Return a WebDriver using an Internet Explorer instance"""
    kwargs = {}
    if capabilities:
        kwargs['capabilities'] = capabilities
    if driver_path is not None:
        kwargs['executable_path'] = driver_path
    return Ie(**kwargs)
