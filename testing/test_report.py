#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testReportWithoutDirectory(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_report(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    report = 'result.html'
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
                                '--webqareport=%s' % report,
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
    report_file = os.path.sep.join([str(testdir.tmpdir), report])
    assert os.path.exists(report_file)
    assert os.path.isfile(report_file)


def testReportWithDirectory(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_report(mozwebqa):
            mozwebqa.selenium.open('/')
            assert mozwebqa.selenium.get_text('css=h1') == 'Success!'
    """)
    report = 'report/result.html'
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--api=rc',
                                '--browser=*firefox',
                                '--webqareport=%s' % report,
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
    report_file = os.path.sep.join([str(testdir.tmpdir), report])
    assert os.path.exists(report_file)
    assert os.path.isfile(report_file)
