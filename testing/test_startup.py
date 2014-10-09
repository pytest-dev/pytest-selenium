#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testBadBaseUrlGeneratesExpectedMessage(testdir, webserver):
    STATUS_CODE = 500

    testdir.makepyfile(test_one="""
        import pytest
        @pytest.mark.skip_selenium
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)
    result = testdir.runpytest('--baseurl=http://localhost:%s/%s/' % (
        webserver.port, STATUS_CODE))
    assert result.ret != 0
    # tracestyle is native by default for hook failures
    result.stdout.fnmatch_lines([
        "*INTERNALERROR*AssertionError*Base URL did not return status code "
        "200 or 401*Response: %s, Headers:*{*}*" % STATUS_CODE
    ])
