# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def pytest_selenium_capture_debug(item, report, extra):
    """ Called when gathering debug information for the HTML report. """


def pytest_selenium_runtest_makereport(item, report, summary, extra):
    """ Called when making the HTML report. """
