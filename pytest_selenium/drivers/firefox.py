# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


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


def driver_kwargs(capabilities, driver_path, firefox_path, firefox_profile,
                  **kwargs):
    kwargs = {}
    if capabilities:
        kwargs['capabilities'] = capabilities
    if driver_path is not None:
        kwargs['executable_path'] = driver_path
    if firefox_path is not None:
        # get firefox binary from options until capabilities support
        kwargs['firefox_binary'] = FirefoxBinary(firefox_path)
    kwargs['firefox_profile'] = firefox_profile
    return kwargs


@pytest.fixture(scope='session')
def firefox_path(request):
    return request.config.getoption('firefox_path')


@pytest.fixture
def firefox_profile(request):
    profile = FirefoxProfile(request.config.getoption('firefox_profile'))
    for preference in request.config.getoption('firefox_preferences'):
        name, value = preference
        if value.isdigit():
            # handle integer preferences
            value = int(value)
        elif value.lower() in ['true', 'false']:
            # handle boolean preferences
            value = value.lower() == 'true'
        profile.set_preference(name, value)
    profile.update_preferences()
    for extension in request.config.getoption('firefox_extensions'):
        profile.add_extension(extension)
    return profile
