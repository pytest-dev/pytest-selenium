# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

HOST = os.environ.get("SELENIUM_HOST", "localhost")
PORT = os.environ.get("SELENIUM_PORT", 4444)


def driver_kwargs(capabilities, host, port, **kwargs):
    host = host if host.startswith("http") else f"http://{host}"
    executor = f"{host}:{port}/wd/hub"

    kwargs = {
        "command_executor": executor,
        "desired_capabilities": capabilities,
    }
    return kwargs
