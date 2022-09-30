# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from selenium.webdriver.edge.options import Options


def driver_kwargs(capabilities, driver_log, driver_path, edge_options, **kwargs):

    kwargs = {
        "service_log_path": driver_log,
        "options": edge_options,
    }

    if capabilities:
        kwargs["capabilities"] = capabilities
    if driver_path is not None:
        kwargs["executable_path"] = driver_path

    return kwargs


@pytest.fixture
def edge_options():
    return Options()
