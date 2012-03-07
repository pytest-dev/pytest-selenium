#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import py
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
    result = testdir.runpytest()
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: --baseurl must be specified.'])


def testShouldFailWithoutBrowserNameWhenUsingWebDriverAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    result = testdir.runpytest('--baseurl=http://localhost:8000')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: --browsername must be specified when using '
                    "the 'webdriver' api."])


def testShouldFailWithoutBrowserVersionWhenUsingWebDriverAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--browsername=firefox')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: -browserver must be specified when using '
                    "the 'webdriver' api."])


def testShouldFailWithoutPlatformWhenUsingWebDriverAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--browsername=firefox',
                               '--browserver=beta')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: -platform must be specified when using the '
                    "'webdriver' api."])


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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--saucelabs=%s' % sauce_labs_credentials)
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ["KeyError: 'username'"])


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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--saucelabs=%s' % sauce_labs_credentials)
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ["KeyError: 'api-key'"])


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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--saucelabs=%s' % sauce_labs_credentials)
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: username must be specified in the sauce labs '
                    'credentials file.'])


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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--saucelabs=%s' % sauce_labs_credentials)
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: api-key must be specified in the sauce labs '
                    'credentials file.'])


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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--api=rc',
                               '--saucelabs=%s' % sauce_labs_credentials)
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: --browsername must be specified when using '
                    "the 'rc' api with sauce labs."])


def testShouldFailWithoutBrowserVersionWhenUsingSauceWithRCAPI(testdir):
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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--api=rc',
                               '--saucelabs=%s' % sauce_labs_credentials,
                               '--browsername=firefox')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: --browserver must be specified when using '
                    "the 'rc' api with sauce labs."])


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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--api=rc',
                               '--saucelabs=%s' % sauce_labs_credentials,
                               '--browsername=firefox',
                               '--browserver=10')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: --platform must be specified when using the '
                    "'rc' api with sauce labs."])


def testShouldFailWithoutBrowserOrEnvironmentWhenUsingRCAPI(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--api=rc')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['UsageError: --browser or --environment must be specified '
                    "when using the 'rc' api."])


def testShouldErrorThatItCantFindTheChromeBinary(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--driver=chrome',
                               '--chromepath=/tmp/chromedriver',
                               '--chromeopts={"binary_location":"foo"}')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ['Could not find Chrome binary at: foo'])
