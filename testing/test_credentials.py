#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testCredentials(testdir, webserver):
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
    result = testdir.runpytest('--baseurl=http://localhost:%s' % webserver.port,
                               '--credentials=%s' % credentials,
                               '--driver=firefox')
    assert result.ret == 0


def testCredentialsKeyError(testdir, webserver):
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
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--credentials=%s' % credentials,
                                '--driver=firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert out == "KeyError: 'password'"
