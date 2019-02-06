# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import sys

pytestmark = pytest.mark.nondestructive


@pytest.mark.skipif(sys.platform != "win32", reason="Edge only runs on Windows")
@pytest.mark.edge
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
    testdir.quick_qa("--driver", "Edge", file_test, passed=1)
