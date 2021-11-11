# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import configparser

from pytest_selenium.exceptions import (
    MissingCloudCredentialError,
    MissingCloudSettingError,
    InvalidCloudSettingError,
)


class Provider(object):
    @property
    def name(self):
        return type(self).__name__

    @property
    def config_name(self):
        return ".{0}".format(self.name.lower())

    @property
    def config_file_path(self):
        return os.path.join(os.path.expanduser("~"), self.config_name)

    @property
    def config(self):
        config = configparser.ConfigParser()
        config.read([self.config_name, self.config_file_path])
        return config

    def get_credential(self, key, envs):
        try:
            return self.get_setting(key, envs, "credentials")
        except MissingCloudSettingError:
            raise MissingCloudCredentialError(self.name, key, envs)

    def get_setting(self, key, envs, section, allowed_values=None):
        value = None
        try:
            value = self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, KeyError):
            for env in envs:
                value = os.getenv(env)
                if value:
                    break

        if value is None:
            raise MissingCloudSettingError(self.name, key, envs)
        if allowed_values and value not in allowed_values:
            raise InvalidCloudSettingError(self.name, key, value)

        return value

    def uses_driver(self, driver):
        return driver.lower() == self.name.lower()
