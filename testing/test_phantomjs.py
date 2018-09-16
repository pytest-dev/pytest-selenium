# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.mark.phantomjs
def test_launch(testdir, httpserver):
    httpserver.serve_content(content="<h1>Success!</h1>")
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(webtext):
            assert webtext == u'Success!'
    """
    )
    testdir.quick_qa("--driver", "PhantomJS", file_test, passed=1)


@pytest.mark.phantomjs
def test_args(testdir):
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.fixture
        def driver_args():
            return ['--webdriver-logfile=foo.log']

        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """
    )
    testdir.quick_qa("--driver", "PhantomJS", file_test, passed=1)
    assert os.path.exists(str(testdir.tmpdir.join("foo.log")))
