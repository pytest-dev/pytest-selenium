# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import sys
from packaging.version import Version
from selenium import __version__ as SELENIUM_VERSION


pytestmark = pytest.mark.nondestructive


@pytest.mark.skipif(sys.platform != "win32", reason="Edge only runs on Windows")
@pytest.mark.edge
def test_launch_legacy(testdir, httpserver):
    httpserver.serve_content(content="<h1>Success!</h1>")
    file_test = testdir.makepyfile(
        """
        import pytest
        @pytest.mark.nondestructive
        def test_pass(webtext):
            assert webtext == u'Success!'
    """
    )
    testdir.quick_qa("--driver", "Edge", file_test, passed=1)


@pytest.mark.skipif(sys.platform != "win32", reason="Edge only runs on Windows")
@pytest.mark.skipif(
    Version(SELENIUM_VERSION) < Version("4.0.0"),
    reason="Edge chromium only supported for selenium >= 4.0.0",
)
@pytest.mark.edge
@pytest.mark.parametrize("use_chromium", [True, False], ids=["chromium", "legacy"])
def test_launch(use_chromium, testdir, httpserver):
    httpserver.serve_content(content="<h1>Success!</h1>")
    file_test = testdir.makepyfile(
        """
        import pytest

        @pytest.mark.nondestructive
        def test_pass(webtext):
            assert webtext == u'Success!'

        @pytest.fixture
        def edge_options(edge_options):
            edge_options.use_chromium = {}
            return edge_options
    """.format(
            use_chromium
        )
    )
    testdir.quick_qa("--driver", "Edge", file_test, passed=1)
