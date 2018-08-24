# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def driver_kwargs(capabilities, driver_path, **kwargs):
    kwargs = {"desired_capabilities": capabilities}
    if driver_path is not None:
        kwargs["executable_path"] = driver_path
    return kwargs
