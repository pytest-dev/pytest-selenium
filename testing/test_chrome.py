# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.fixture
def testfile(testdir):
    return testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """)


def failure_with_output(testdir, *args, **kwargs):
    reprec = testdir.inline_run(*args, **kwargs)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    return out


@pytest.fixture
def failure(testdir, testfile, webserver_base_url):
    return partial(failure_with_output, testdir, testfile, webserver_base_url)


def test_missing_chrome_binary(failure):
    out = failure('--driver=chrome',
                  '--chromeopts={"binary_location":"foo"}')
    if 'ChromeDriver executable needs to be available in the path' in out:
        pytest.fail('You must have Chrome Driver installed on your path for '
                    'this test to run correctly. For further information see '
                    'pytest-selenium documentation.')
    assert 'Could not find Chrome binary at: foo' in out


@pytest.mark.chrome
def test_proxy(testdir, webserver_base_url, webserver):
    """Test that a proxy can be set for Chrome."""
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(selenium):
            selenium.get('http://example.com')
            header = selenium.find_element_by_tag_name('h1')
            assert header.text == 'Success!'
    """)
    testdir.quick_qa(webserver_base_url,
                     '--driver=chrome',
                     '--proxyhost=localhost',
                     '--proxyport=%s' % webserver.port, file_test, passed=1)
