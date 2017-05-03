# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import re

import pytest

pytestmark = pytest.mark.nondestructive

LOG_REGEX = '<a class="text" href=".*" target="_blank">Driver Log</a>'


def test_driver_log(testdir, httpserver):
    httpserver.serve_content(content='<h1>Success!</h1>')
    testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_fail(webtext):
            assert False
    """)
    path = testdir.tmpdir.join('report.html')
    testdir.runpytestqa('--html', path)
    with open(str(path)) as f:
        html = f.read()
    assert re.search(LOG_REGEX, html) is not None
    assert os.path.exists(str(testdir.tmpdir.join('driver.log')))


def test_driver_log_fixture(testdir, httpserver):
    httpserver.serve_content(content='<h1>Success!</h1>')
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def driver_log():
            return 'foo.log'

        @pytest.mark.nondestructive
        def test_pass(webtext):
            assert webtext == u'Success!'
    """)
    testdir.quick_qa(file_test, passed=1)
    assert os.path.exists(str(testdir.tmpdir.join('foo.log')))


def test_no_driver_log(testdir, httpserver):
    httpserver.serve_content(content='<h1>Success!</h1>')
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def driver_log():
            return None

        @pytest.mark.nondestructive
        def test_fail(webtext):
            assert False
    """)
    path = testdir.tmpdir.join('report.html')
    testdir.runpytestqa('--html', path)
    with open(str(path)) as f:
        html = f.read()
    assert re.search(LOG_REGEX, html) is None
    assert not os.path.exists(str(testdir.tmpdir.join('driver.log')))
