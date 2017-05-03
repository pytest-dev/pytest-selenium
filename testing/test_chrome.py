# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import pytest

pytestmark = pytest.mark.nondestructive


@pytest.mark.chrome
def test_launch(testdir, httpserver):
    httpserver.serve_content(content='<h1>Success!</h1>')
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(webtext):
            assert webtext == u'Success!'
    """)
    testdir.quick_qa('--driver', 'Chrome', file_test, passed=1)


@pytest.mark.chrome
def test_options(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def chrome_options(chrome_options):
            chrome_options.binary_location = '/foo/bar'
            return chrome_options

        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """)
    reprec = testdir.inline_run('--driver', 'Chrome')
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    assert 'no chrome binary at /foo/bar' in out


@pytest.mark.chrome
def test_args(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.fixture
        def driver_log():
            return None

        @pytest.fixture
        def driver_args():
            return ['--log-path=foo.log']

        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """)
    testdir.quick_qa('--driver', 'Chrome', file_test, passed=1)
    assert os.path.exists(str(testdir.tmpdir.join('foo.log')))
