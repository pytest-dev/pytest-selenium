# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import warnings
import os

import pytest
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options


def pytest_addoption(parser):
    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--firefox-path',
                     metavar='path',
                     help='path to the firefox binary.')
    group._addoption('--firefox-preference',
                     action='append',
                     default=[],
                     dest='firefox_preferences',
                     metavar=('name', 'value'),
                     nargs=2,
                     help='additional firefox preferences.')
    group._addoption('--firefox-profile',
                     metavar='path',
                     help='path to the firefox profile.')
    group._addoption('--firefox-extension',
                     action='append',
                     default=[],
                     dest='firefox_extensions',
                     metavar='path',
                     help='path to a firefox extension.')


def driver_kwargs(capabilities, driver_path, firefox_options, log_path,
                  pytestconfig, **kwargs):
    kwargs = {}
    if capabilities:
        kwargs['capabilities'] = capabilities
    if driver_path is not None:
        kwargs['executable_path'] = driver_path
    log_path = os.path.realpath('geckodriver.log')
    kwargs['log_path'] = pytestconfig._driver_log = log_path
    kwargs['firefox_options'] = firefox_options
    return kwargs


@pytest.fixture
def firefox_options(request, firefox_path, firefox_profile):
    options = Options()
    options.profile = firefox_profile
    if firefox_path is not None:
        options.binary = FirefoxBinary(firefox_path)
    return options


@pytest.fixture(scope='session')
def firefox_path(pytestconfig):
    if pytestconfig.getoption('firefox_path'):
        warnings.warn(
            '--firefox-path has been deprecated and will be removed in a '
            'future release. Please make sure the Firefox binary is in the '
            'default location, or the system path. If you want to specify a '
            'binary path then use the firefox_options fixture to and set this '
            'using firefox_options.binary.', DeprecationWarning)
        return pytestconfig.getoption('firefox_path')


@pytest.fixture
def firefox_profile(pytestconfig):
    profile = None
    if pytestconfig.getoption('firefox_profile'):
        profile = FirefoxProfile(pytestconfig.getoption('firefox_profile'))
        warnings.warn(
            '--firefox-profile has been deprecated and will be removed in '
            'a future release. Please use the firefox_options fixture to '
            'set a profile path or FirefoxProfile object using '
            'firefox_options.profile.', DeprecationWarning)
    if pytestconfig.getoption('firefox_preferences'):
        profile = profile or FirefoxProfile()
        warnings.warn(
            '--firefox-preference has been deprecated and will be removed in '
            'a future release. Please use the firefox_options fixture to set '
            'preferences using firefox_options.set_preference. If you are '
            'using Firefox 47 or earlier then you will need to create a '
            'FirefoxProfile object with preferences and set this using '
            'firefox_options.profile.', DeprecationWarning)
        for preference in pytestconfig.getoption('firefox_preferences'):
            name, value = preference
            if value.isdigit():
                # handle integer preferences
                value = int(value)
            elif value.lower() in ['true', 'false']:
                # handle boolean preferences
                value = value.lower() == 'true'
            profile.set_preference(name, value)
        profile.update_preferences()
    if pytestconfig.getoption('firefox_extensions'):
        profile = profile or FirefoxProfile()
        warnings.warn(
            '--firefox-extensions has been deprecated and will be removed in '
            'a future release. Please use the firefox_options fixture to '
            'create a FirefoxProfile object with extensions and set this '
            'using firefox_options.profile.', DeprecationWarning)
        for extension in pytestconfig.getoption('firefox_extensions'):
            profile.add_extension(extension)
    return profile
