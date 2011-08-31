#!/usr/bin/env python
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla WebQA Tests.
#
# The Initial Developer of the Original Code is Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s): Dave Hunt <dhunt@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import pytest

from webserver import SimpleWebServer

def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestUsage.webserver = webserver

def teardown_module(module):
    TestUsage.webserver.stop()

@pytest.mark.skip_selenium
class TestUsage:

    def testShouldFailWithoutBaseURL(self, testdir):
        file_test = testdir.makepyfile("""
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
            def test_selenium(mozwebqa):
                assert True
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--api=rc', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "UsageError: --browser or --environment must be specified when using the 'rc' api."
