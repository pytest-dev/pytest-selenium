#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testStartWebDriverClient(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            mozwebqa.selenium.get('http://localhost:8000/')
            header = mozwebqa.selenium.find_element_by_tag_name('h1')
            assert header.text == 'Success!'
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:8000',
                                '--api=webdriver',
                                '--driver=firefox',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1
