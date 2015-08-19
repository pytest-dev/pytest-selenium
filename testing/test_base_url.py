# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytest.mark.nondestructive


def failure_with_output(testdir, *args, **kwargs):
    reprec = testdir.inline_run(*args, **kwargs)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    return out


def test_missing_base_url(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(selenium): pass
    """)
    out = failure_with_output(testdir, file_test)
    assert 'UsageError: --base-url must be specified.' in out


def test_fixture(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.fixture(scope='session')
        def base_url():
            return 'foo'
        @pytest.fixture(scope='session')
        def _verify_base_url():
            pass
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


def test_failing_base_url(testdir, webserver):
    status_code = 500
    base_url = 'http://localhost:{0}/{1}/'.format(webserver.port, status_code)
    testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_pass(): pass
    """.format(base_url))
    result = testdir.runpytest('--base-url', base_url)
    assert result.ret != 0
    # tracestyle is native by default for hook failures
    result.stdout.fnmatch_lines([
        '*UsageError: Base URL did not respond with one of the following '
        'status codes: *.',
        '*URL: {0}*'.format(base_url),
        '*Response status code: {0}*'.format(status_code),
        '*Response headers: {*}*'])
