# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def test_should_fail_without_username(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run(
        '--driver=saucelabs',
        '--skipurlcheck',
        '--baseurl=http://localhost',
        '--browsername=firefox', file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'ValueError: Sauce Labs username must be set!'


def test_should_fail_without_api_key(testdir, monkeypatch):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run(
        '--driver=saucelabs',
        '--skipurlcheck',
        '--baseurl=http://localhost',
        '--browsername=firefox', file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'ValueError: Sauce Labs API key must be set!'


def test_should_fail_with_invalid_credentials(testdir, monkeypatch):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run(
        '--driver=saucelabs',
        '--skipurlcheck',
        '--baseurl=http://localhost',
        '--browsername=firefox', file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert re.search('(auth failed)|(Sauce Labs Authentication Error)', out)


def test_should_fail_without_browser_name(testdir, monkeypatch):
    monkeypatch.setenv('SAUCELABS_USERNAME', 'foo')
    monkeypatch.setenv('SAUCELABS_API_KEY', 'bar')
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run(
        '--driver=saucelabs',
        '--skipurlcheck',
        '--baseurl=http://localhost', file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'ValueError: Sauce Labs requires a browser name!'
