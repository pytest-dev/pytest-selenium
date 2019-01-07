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
    def name(self):
        return type(self).__name__

    @property
    def config(self):
        name = ".{0}".format(self.name.lower())
        config = configparser.ConfigParser()
        config.read([name, os.path.join(os.path.expanduser("~"), name)])
        return config

    def get_credential(self, key, envs):
        try:
            return self.config.get("credentials", key)
        except (configparser.NoSectionError, configparser.NoOptionError, KeyError):
            for env in envs:
                value = os.getenv(env)
                if value:
                    return value
        raise MissingCloudCredentialError(self.name, key, envs)

    def uses_driver(self, driver):
        return driver.lower() == self.name.lower()


def get_markers(node):
    # `MarkInfo` is removed in pytest 4.1.0
    # see https://github.com/pytest-dev/pytest/pull/4564
    try:
        from _pytest.mark import MarkInfo

        keywords = node.keywords
        markers = [m for m in keywords.keys() if isinstance(keywords[m], MarkInfo)]
    except ImportError:
        # `iter_markers` was introduced in pytest 3.6
        markers = [m.name for m in node.iter_markers()]

    return markers
