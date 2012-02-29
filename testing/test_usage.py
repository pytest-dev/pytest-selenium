#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from webserver import SimpleWebServer


def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestUsage.webserver = webserver


def teardown_module(module):
    TestUsage.webserver.stop()


@pytest.mark.skip_selenium
@pytest.mark.nondestructive
class TestUsage:

    def testShouldFailWithoutBaseURL(self, testdir):
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

    def testShouldFailWithoutBrowserNameWhenUsingWebDriverAPI(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                assert True
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --browsername must be specified when using the 'webdriver' api."

    def testShouldFailWithoutBrowserVersionWhenUsingWebDriverAPI(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                assert True
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--browsername=firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --browserver must be specified when using the 'webdriver' api."

    def testShouldFailWithoutPlatformWhenUsingWebDriverAPI(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                assert True
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--browsername=firefox', '--browserver=beta', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --platform must be specified when using the 'webdriver' api."

    def testShouldFailWithoutSauceLabsUser(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                assert True
        """)
        sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
            api-key: api-key
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--saucelabs=%s' % sauce_labs_credentials, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "KeyError: 'username'"

    def testShouldFailWithoutSauceLabsKey(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                assert True
        """)
        sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
            username: username
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--saucelabs=%s' % sauce_labs_credentials, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "KeyError: 'api-key'"

    def testShouldFailWithBlankSauceLabsUser(self, testdir):
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
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--saucelabs=%s' % sauce_labs_credentials, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == 'UsageError: username must be specified in the sauce labs credentials file.'

    def testShouldFailWithBlankSauceLabsKey(self, testdir):
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
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--saucelabs=%s' % sauce_labs_credentials, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == 'UsageError: api-key must be specified in the sauce labs credentials file.'

    def testShouldFailWithoutBrowserNameWhenUsingSauceWithRCAPI(self, testdir):
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
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--saucelabs=%s' % sauce_labs_credentials, file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --browsername must be specified when using the 'rc' api with sauce labs."

    def testShouldFailWithoutBrowserVersionWhenUsingSauceWithRCAPI(self, testdir):
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
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--saucelabs=%s' % sauce_labs_credentials, '--browsername=firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --browserver must be specified when using the 'rc' api with sauce labs."

    def testShouldFailWithoutPlatformWhenUsingSauceWithRCAPI(self, testdir):
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
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', '--saucelabs=%s' % sauce_labs_credentials, '--browsername=firefox', '--browserver=6', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --platform must be specified when using the 'rc' api with sauce labs."

    def testShouldFailWithoutBrowserOrEnvironmentWhenUsingRCAPI(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                assert True
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --browser or --environment must be specified when using the 'rc' api."

    def testShouldErrorThatItCantFindTheChromeBinary(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.nondestructive
            def test_selenium(mozwebqa):
                assert True
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=webdriver',
            '--driver=chrome', '--chromepath=/tmp/chromedriver', '--chromeopts={"binary_location":"foo"}', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        assert "Could not find Chrome binary at: foo" in failed[0].longrepr.reprcrash.message 
