#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import py
import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testCredentials(testdir):
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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--credentials=%s' % credentials,
                               '--driver=firefox')
    assert result.ret == 0


def testCredentialsKeyError(testdir):
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
    result = testdir.runpytest('--baseurl=http://localhost:8000',
                               '--credentials=%s' % credentials,
                               '--driver=firefox')
    assert result.ret == 0
    py.test.raises(Exception,
                   result.stdout.fnmatch_lines,
                   ["KeyError: 'password'"])
