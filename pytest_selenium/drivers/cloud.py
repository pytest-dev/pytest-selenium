# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from pytest_selenium.exceptions import MissingCloudCredentialError

if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser


class Provider(object):

    @property
    def driver(self):
        return type(self).__name__

    @property
    def name(self):
        return self.driver

    @property
    def config(self):
        name = '.{0}'.format(self.driver.lower())
        config = configparser.ConfigParser()
        config.read([name, os.path.join(os.path.expanduser('~'), name)])
        return config

    def get_credential(self, key, envs):
        for env in envs:
            try:
                value = self.config.get('credentials', key)
            except (configparser.NoSectionError,
                    configparser.NoOptionError,
                    KeyError):
                value = os.getenv(env)
            if value:
                return value
        raise MissingCloudCredentialError(self.name, key, envs)

    def get_jenkins_credential(self, key):
        if 'username' == key:
            return os.getenv(self.name.replace(' ', '').upper() + '_USR')
        elif 'key' == key:
            return os.getenv(self.name.replace(' ', '').upper() + '_PSW')
