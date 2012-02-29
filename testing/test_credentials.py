#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from webserver import SimpleWebServer


def setup_module(module):
    webserver = SimpleWebServer()
    webserver.start()
    TestCredentials.webserver = webserver


def teardown_module(module):
    TestCredentials.webserver.stop()


@pytest.mark.skip_selenium
@pytest.mark.nondestructive
class TestCredentials:

    def testCredentials(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.skip_selenium
            @pytest.mark.nondestructive
            def test_credentials(mozwebqa):
                assert mozwebqa.credentials['default']['username'] == 'aUsername'
                assert mozwebqa.credentials['default']['password'] == 'aPassword'
        """)
        credentials = testdir.makefile('.yaml', credentials="""
            default:
                username: aUsername
                password: aPassword
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--credentials=%s' % credentials, '--driver=firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(passed) == 1

    def testCredentialsKeyError(self, testdir):
        file_test = testdir.makepyfile("""
            import pytest
            @pytest.mark.skip_selenium
            @pytest.mark.nondestructive
            def test_credentials(mozwebqa):
                assert mozwebqa.credentials['default']['password'] == 'aPassword'
        """)
        credentials = testdir.makefile('.yaml', credentials="""
            default:
                username: aUsername
        """)
        reprec = testdir.inline_run('--baseurl=http://localhost:%s' % self.webserver.port, '--credentials=%s' % credentials, '--driver=firefox', file_test)
        passed, skipped, failed = reprec.listoutcomes()
        assert len(failed) == 1
        out = failed[0].longrepr.reprcrash.message
        assert out == "KeyError: 'password'"
