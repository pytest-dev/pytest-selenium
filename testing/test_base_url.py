# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


def test_fixture(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.fixture(scope='session')
        def base_url():
            return 'foo'
        @pytest.mark.nondestructive
        def test_fixture(base_url):
            assert base_url == 'foo'
    """)
    testdir.quick_qa(file_test, passed=1)


def test_funcarg(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_funcarg(base_url):
            assert base_url == 'http://localhost:{0}'
    """.format(webserver.port))
    testdir.quick_qa(file_test, passed=1)


def test_config(testdir, webserver):
    base_url = 'http://localhost:{0}/foo'.format(webserver.port)
    testdir.makefile('.ini', pytest="""
        [pytest]
        base_url={0}
    """.format(base_url))
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_config(request, base_url):
            assert request.config.getvalue('base_url') == '{0}'
            assert request.config.getini('base_url') == '{0}'
            assert base_url == '{0}'
    """.format(base_url))
    reprec = testdir.inline_run(file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def test_skip_config(testdir, webserver):
    base_url = 'http://localhost:{0}/foo'.format(webserver.port)
    testdir.makefile('.ini', pytest="""
        [pytest]
        base_url={0}
    """.format(base_url))
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        @pytest.mark.skipif(pytest.config.getoption('base_url') == '{0}',
                            reason='skip')
        def test_skip_config(): pass
    """.format(base_url))
    reprec = testdir.inline_run(file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(skipped) == 1
