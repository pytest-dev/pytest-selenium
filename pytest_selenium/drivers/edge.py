# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from distutils.version import LooseVersion
from selenium import __version__ as SELENIUM_VERSION


def driver_kwargs(capabilities, driver_log, driver_path, **kwargs):

    # Selenium 3.14.0 deprecated log_path in favour of service_log_path
    if LooseVersion(SELENIUM_VERSION) < LooseVersion("3.14.0"):
        kwargs = {"log_path": driver_log}
    else:
        kwargs = {"service_log_path": driver_log}

    if capabilities:
        kwargs["capabilities"] = capabilities
    if driver_path is not None:
        kwargs["executable_path"] = driver_path
    return kwargs
