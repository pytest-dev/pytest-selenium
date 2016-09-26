# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from selenium.webdriver import Safari


@pytest.fixture
def safari_driver(request, capabilities):
    """Return a WebDriver using a Safari instance"""
    kwargs = {}
    if capabilities:
        kwargs['desired_capabilities'] = capabilities
    return Safari(**kwargs)
