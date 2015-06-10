# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.mark.opera
def test_proxy(testdir, webserver_base_url, webserver):
    """Test that a proxy can be set for Opera."""
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(selenium):
            selenium.get('http://example.com')
            header = selenium.find_element_by_tag_name('h1')
            assert header.text == 'Success!'
    """)
    testdir.quick_qa(webserver_base_url,
                     '--driver=opera',
                     '--proxyhost=localhost',
                     '--proxyport=%s' % webserver.port, file_test, passed=1)
