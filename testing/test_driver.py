# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.fixture
def testfile(testdir):
    return testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """)


def failure_with_output(testdir, *args, **kwargs):
    reprec = testdir.inline_run(*args, **kwargs)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    return out


@pytest.fixture
def failure(testdir, testfile, httpserver_base_url):
    return partial(failure_with_output, testdir, testfile, httpserver_base_url)


def test_missing_driver(failure):
    out = failure()
    assert 'UsageError: --driver must be specified' in out


def test_driver_quit(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_driver_quit(selenium):
            selenium.quit()
            selenium.title
    """)
    result = testdir.runpytestqa()
    result.stdout.fnmatch_lines_random([
        'WARNING: Failed to gather URL: *',
        'WARNING: Failed to gather screenshot: *',
        'WARNING: Failed to gather HTML: *',
        'WARNING: Failed to gather log types: *'])
    outcomes = result.parseoutcomes()
    assert outcomes.get('failed') == 1
