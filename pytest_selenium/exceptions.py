# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest


class MissingCloudSettingError(pytest.UsageError):
    def __init__(self, driver, key, envs):
        super(MissingCloudSettingError, self).__init__(
            "{0} {1} must be set. Try setting one of the following "
            "environment variables {2}, or see the documentation for "
            "how to use a configuration file.".format(driver, key, envs)
        )


class MissingCloudCredentialError(MissingCloudSettingError):
    pass


class InvalidCloudSettingError(pytest.UsageError):
    def __init__(self, driver, key, value):
        super(InvalidCloudSettingError, self).__init__(
            "{0} {1} invalid value `{2}`, see the documentation for how "
            "to use this parameter.".format(driver, key, value)
        )
