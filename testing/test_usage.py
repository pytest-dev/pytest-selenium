#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testShouldFailWithoutBaseURL(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run(file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: --baseurl must be specified.'


def testShouldFailWithoutBrowserNameWhenUsingWebDriverAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000', file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: --browsername must be specified when using ' \
                  "the 'webdriver' api."


def testShouldFailWithoutPlatformWhenUsingWebDriverAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--browsername=firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: --platform must be specified when using the ' \
                  "'webdriver' api."


def testShouldFailWithoutSauceLabsUser(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        api-key: api-key
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--saucelabs=%s' % sauce_labs_credentials,
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == "KeyError: 'username'"


def testShouldFailWithoutSauceLabsKey(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username: username
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--saucelabs=%s' % sauce_labs_credentials,
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == "KeyError: 'api-key'"


def testShouldFailWithBlankSauceLabsUser(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username:
        api-key: api-key
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--saucelabs=%s' % sauce_labs_credentials,
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: username must be specified in the sauce labs ' \
                  'credentials file.'


def testShouldFailWithBlankSauceLabsKey(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username: username
        api-key:
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--saucelabs=%s' % sauce_labs_credentials,
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: api-key must be specified in the sauce labs ' \
                  'credentials file.'


def testShouldFailWithoutBrowserNameWhenUsingSauceWithRCAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username: username
        api-key: api-key
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=rc',
                                '--saucelabs=%s' % sauce_labs_credentials,
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: --browsername must be specified when using ' \
                  "the 'rc' api with sauce labs."


def testShouldFailWithoutPlatformWhenUsingSauceWithRCAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username: username
        api-key: api-key
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=rc',
                                '--saucelabs=%s' % sauce_labs_credentials,
                                '--browsername=firefox',
                                '--browserver=10',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: --platform must be specified when using the ' \
                  "'rc' api with sauce labs."


def testShouldFailWithoutBrowserOrEnvironmentWhenUsingRCAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=rc',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == 'UsageError: --browser or --environment must be specified ' \
                  "when using the 'rc' api."


def testShouldErrorThatItCantFindTheChromeBinary(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--driver=chrome',
                                '--chromepath=/tmp/chromedriver',
                                '--chromeopts={"binary_location":"foo"}',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert "Could not find Chrome binary at: foo" in failed[0].longrepr.reprcrash.message 
