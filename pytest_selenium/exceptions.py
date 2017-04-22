# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest


class MissingCloudCredentialError(pytest.UsageError):

    def __init__(self, driver, key, envs):
        super(MissingCloudCredentialError, self).__init__(
            '{0} {1} must be set. Try setting one of the following '
            'environment variables {2}, or see the documentation for '
            'how to use a configuration file.'.format(driver, key, envs))
